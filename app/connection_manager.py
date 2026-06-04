"""In-memory tracker of WebSocket connections per room.

Single-server only. Stage 2+ replaces this with Redis pub/sub
so multiple backend instances can coordinate.
"""
from typing import Dict, List
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    def __init__(self) -> None:
        # room_code -> list of (user_id, websocket) tuples
        self._rooms: Dict[str, List[tuple[int, WebSocket]]] = {}
        self._pending_forfeits: Dict[tuple, asyncio.Task] = {}
        self._latest_code: Dict[tuple, str] = {}
    
    def set_code(self, room_code: str, user_id: int, code: str) -> None:
        self._latest_code[(room_code, user_id)] = code

    def get_code(self, room_code: str, user_id: int) -> str | None:
        return self._latest_code.get((room_code, user_id))

    async def connect(self, room_code: str, user_id: int, websocket: WebSocket) -> None:
        """Accept the socket and register it under its room."""
        await websocket.accept()
        self._rooms.setdefault(room_code, []).append((user_id, websocket))

    def disconnect(self, room_code: str, websocket: WebSocket) -> None:
        """Remove a socket from its room. Safe to call even if not present."""
        conns = self._rooms.get(room_code, [])
        self._rooms[room_code] = [(uid, ws) for (uid, ws) in conns if ws is not websocket]
        if not self._rooms[room_code]:
            del self._rooms[room_code]
    
    def schedule_forfeit(self, room_code: str, user_id: int, coro) -> None:
        """Start a delayed forfeit task for (room, user). Cancels any existing one first."""
        self.cancel_forfeit(room_code, user_id)
        key = (room_code, user_id)
        self._pending_forfeits[key] = asyncio.create_task(coro)

    def cancel_forfeit(self, room_code: str, user_id: int) -> None:
        """Cancel a pending forfeit for (room, user), if any (e.g. they reconnected)."""
        key = (room_code, user_id)
        task = self._pending_forfeits.pop(key, None)
        if task and not task.done():
            task.cancel()

    def connected_user_ids(self, room_code: str) -> set[int]:
        """Return the set of user ids currently connected to a room."""
        return {uid for (uid, _) in self._rooms.get(room_code, [])}

    async def broadcast(self, room_code: str, sender: WebSocket, message: dict) -> None:
        """Send a JSON message to every socket in a room. Drops broken ones."""
        conns = list(self._rooms.get(room_code, []))
        for uid, ws in conns:
            if ws is sender:
                continue  # Don't send to the sender
            try:
                await ws.send_json(message)
            except Exception:
                # Socket is broken/closed; remove it
                self.disconnect(room_code, ws)
    
    async def broadcast_all(self, room_code: str, message: dict) -> None:
        """Send a JSON message to every socket in a room, including the sender."""
        conns = list(self._rooms.get(room_code, []))
        for uid, ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_code, ws)
                


# Module-level singleton — one shared manager for the whole app
manager = ConnectionManager()