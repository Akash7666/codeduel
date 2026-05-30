from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    statement = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False, default="easy")
    starter_code = Column(Text, nullable=False)
    function_name = Column(String(100), nullable=False)
    reference_solution = Column(Text, nullable=False)
    time_limit_sec = Column(Integer, nullable=False, default=2)
    memory_limit_mb = Column(Integer, nullable=False, default=128)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    test_cases = relationship(
        "TestCase", back_populates="problem", cascade="all, delete-orphan"
    )

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)

    problem = relationship("Problem", back_populates="test_cases")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="waiting")
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    player_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_b_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    @property
    def difficulty(self):
        return self.problem.difficulty if self.problem else None

    problem = relationship("Problem")
    player_a = relationship("User", foreign_keys=[player_a_id])
    player_b = relationship("User", foreign_keys=[player_b_id])
    winner = relationship("User", foreign_keys=[winner_id])
    player_a_tab_switches = Column(Integer, nullable=False, default=0)
    player_b_tab_switches = Column(Integer, nullable=False, default=0)
    submissions = relationship(
        "Submission", back_populates="room", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(Text, nullable=False)
    passed = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    all_passed = Column(Boolean, nullable=False, default=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="submissions")
    user = relationship("User")