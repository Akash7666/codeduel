"""WebSocket endpoint for live duels."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Room
from app.dependencies import get_user_from_token
from app.connection_manager import manager
from datetime import datetime, timezone

router = APIRouter()


def _room_state_message(room: Room) -> dict:
    """Build the snapshot of room state sent to a newly connected player."""
    return {
        "type": "room_state",
        "room": {
            "code": room.code,
            "status": room.status,
            "problem_id": room.problem_id,
            "player_a": {"id": room.player_a.id, "username": room.player_a.username},
            "player_b": (
                {"id": room.player_b.id, "username": room.player_b.username}
                if room.player_b else None
            ),
            "winner_id": room.winner_id,
            "started_at": room.started_at.isoformat() if room.started_at else None,
            "finished_at": room.finished_at.isoformat() if room.finished_at else None,
        },
    }

def _duel_started_message(room: Room) -> dict:
    """Payload sent to both players when the duel begins."""
    problem = room.problem
    visible_cases = [
        {"input": tc.input_data, "expected": tc.expected_output}
        for tc in problem.test_cases
        if not tc.is_hidden
    ]
    return {
        "type": "duel_started",
        "started_at": room.started_at.isoformat(),
        "problem": {
            "slug": problem.slug,
            "title": problem.title,
            "statement": problem.statement,
            "starter_code": problem.starter_code,
            "function_name": problem.function_name,
            "time_limit_sec": problem.time_limit_sec,
            "visible_test_cases": visible_cases,
        },
    }



@router.websocket("/ws/rooms/{code}")
async def room_socket(
    websocket: WebSocket,
    code: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # 1. Authenticate
    user = get_user_from_token(token, db)
    if user is None:
        await websocket.close(code=4401, reason="Invalid or expired token")
        return

    # 2. Find the room
    room = db.query(Room).filter(Room.code == code.upper()).first()
    if room is None:
        await websocket.close(code=4404, reason="Room not found")
        return

    # 3. Reject anyone who isn't a player in this room
    if user.id not in {room.player_a_id, room.player_b_id}:
        await websocket.close(code=4403, reason="Not a player in this room")
        return

    # 4. Accept and register
    await manager.connect(room.code, user.id, websocket)

    # 5. Send room snapshot to the new joiner; notify the other side
    try:
        await websocket.send_json(_room_state_message(room))
        await manager.broadcast(
            room.code,
            websocket,
            {"type": "player_joined", "user_id": user.id, "username": user.username},
        )

        # If both players are now connected and the duel hasn't started, go live.
        connected = manager.connected_user_ids(room.code)
        both_present = (
            room.player_b_id is not None
            and room.player_a_id in connected
            and room.player_b_id in connected
        )
        if both_present and room.status == "waiting":
            room.status = "live"
            room.started_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(room)
            await manager.broadcast_all(room.code, _duel_started_message(room))

        # Keep the connection open. We don't expect client->server messages yet,
        # but receive_text() will sit here and raise WebSocketDisconnect on drop.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room.code, websocket)
        await manager.broadcast(
            room.code,
            websocket,
            {"type": "player_left", "user_id": user.id, "username": user.username},
        )