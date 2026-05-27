import random
import string
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Room, Problem, User
from app.dependencies import get_current_user
from app.schemas_rooms import RoomOut

router = APIRouter(prefix="/rooms", tags=["rooms"])

CODE_ALPHABET = string.ascii_uppercase + string.digits  # A-Z, 0-9
CODE_LENGTH = 6


def _generate_code() -> str:
    return "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))

@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Pick a random problem
    problem = db.query(Problem).order_by(func.random()).first()
    if not problem:
        raise HTTPException(status_code=500, detail="No problems available")

    # Try up to 10 unique codes — collisions are astronomically rare
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