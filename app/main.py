from fastapi import FastAPI
from app.auth import router as auth_router

app = FastAPI(title="CodeDuel API")

app.include_router(auth_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "CodeDuel API is running"}