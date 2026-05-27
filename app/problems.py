from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Problem
from app.judging import judge_submission

router = APIRouter(prefix="/problems", tags=["problems"])


class SubmitCode(BaseModel):
    code: str


@router.post("/{slug}/test-judge")
def test_judge(slug: str, data: SubmitCode, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    verdict = judge_submission(data.code, problem)
    return verdict