from fastapi import FastAPI

app = FastAPI(title="CodeDuel API")


@app.get("/")
def root():
    return {"status": "ok", "message": "CodeDuel API is running"}