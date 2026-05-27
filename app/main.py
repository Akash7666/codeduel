from fastapi import FastAPI
from app.auth import router as auth_router
from app.problems import router as problems_router
from app.rooms import router as rooms_router




app = FastAPI(title="CodeDuel API")

app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(rooms_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "CodeDuel API is running"}