from fastapi import FastAPI
from app.auth import router as auth_router
from app.problems import router as problems_router
from app.rooms import router as rooms_router
from app.websockets import router as ws_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse





app = FastAPI(title="CodeDuel API")

app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(rooms_router)
app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse("static/login.html")

@app.get("/lobby")
def serve_lobby():
    return FileResponse("static/lobby.html")