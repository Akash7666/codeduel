import random
import string
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Room, Problem, User
from app.dependencies import get_current_user
from app.schemas import CreateRoomRequest
from app.schemas_rooms import RoomOut, SubmitCode

from datetime import datetime, timezone
from app.connection_manager import manager
from app.judging import judge_submission
from app.models import Submission


router = APIRouter(prefix="/rooms", tags=["rooms"])

CODE_ALPHABET = string.ascii_uppercase + string.digits  # A-Z, 0-9
CODE_LENGTH = 6


def _generate_code() -> str:
    return "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))

@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    data: CreateRoomRequest = CreateRoomRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Pick a random problem of the requested difficulty
    problem = (
        db.query(Problem)
        .filter(Problem.difficulty == data.difficulty)
        .order_by(func.random())
        .first()
    )
    if not problem:
        raise HTTPException(
            status_code=400,
            detail=f"No problems available for difficulty '{data.difficulty}'",
        )

    for _ in range(10):
        room = Room(
            code=_generate_code(),
            status="waiting",
            problem_id=problem.id,
            player_a_id=current_user.id,
        )
        db.add(room)
        try:
            db.commit()
            db.refresh(room)
            return room
        except IntegrityError:
            db.rollback()
    raise HTTPException(status_code=500, detail="Could not generate unique room code")


@router.post("/{code}/join", response_model=RoomOut)
def join_room(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.code == code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="Room is no longer accepting players")
    if room.player_a_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot join your own room")
    if room.player_b_id is not None:
        raise HTTPException(status_code=400, detail="Room is full")

    room.player_b_id = current_user.id
    db.commit()
    db.refresh(room)
    return room


@router.get("/{code}", response_model=RoomOut)
def get_room(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.code == code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

def _record_result(db: Session, room: Room) -> None:
    """Increment win/loss counts based on the room's winner."""
    if room.winner_id is None:
        return
    loser_id = room.player_b_id if room.winner_id == room.player_a_id else room.player_a_id
    winner = db.query(User).filter(User.id == room.winner_id).first()
    loser = db.query(User).filter(User.id == loser_id).first()
    if winner:
        winner.wins += 1
    if loser:
        loser.losses += 1






@router.post("/{code}/submit")
async def submit_code(
    code: str,
    data: "SubmitCode",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.code == code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if current_user.id not in {room.player_a_id, room.player_b_id}:
        raise HTTPException(status_code=403, detail="Not a player in this room")
    if room.status != "live":
        raise HTTPException(status_code=400, detail="Duel is not live")

    # Judge the code (this calls Judge0 for each test case)
    verdict = judge_submission(data.code, room.problem)

    # Record the submission with a server-side timestamp
    submission = Submission(
        room_id=room.id,
        user_id=current_user.id,
        code=data.code,
        passed=verdict["passed"],
        total=verdict["total"],
        all_passed=verdict["all_passed"],
    )
    db.add(submission)
    db.commit()

    # Tell the opponent that this player attempted
    await manager.broadcast(
        room.code,
        None,  # no sender to skip; broadcast to everyone
        {
            "type": "opponent_submitted",
            "user_id": current_user.id,
            "username": current_user.username,
            "passed": verdict["passed"],
            "total": verdict["total"],
            "all_passed": verdict["all_passed"],
        },
    )

    # First correct solution wins — guard on status to handle ties
    if verdict["all_passed"] and room.status == "live":
        room.status = "finished"
        room.winner_id = current_user.id
        room.finished_at = datetime.now(timezone.utc)
        _record_result(db, room)
        db.commit()
        db.refresh(room)
        await manager.broadcast_all(
            room.code,
            {
                "type": "duel_ended",
                "winner_id": room.winner_id,
                "winner_username": current_user.username,
                "finished_at": room.finished_at.isoformat(),
            },
        )

    return verdict