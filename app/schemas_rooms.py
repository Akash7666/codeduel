from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PlayerInfo(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class RoomOut(BaseModel):
    code: str
    status: str
    problem_id: int
    player_a: PlayerInfo
    player_b: Optional[PlayerInfo] = None
    winner_id: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)