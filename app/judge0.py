"""Thin client for the Judge0 code execution API."""
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

JUDGE0_URL = os.getenv("JUDGE0_URL")
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY")
JUDGE0_API_HOST = os.getenv("JUDGE0_API_HOST")

PYTHON_LANGUAGE_ID = 71


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": JUDGE0_API_KEY,
        "X-RapidAPI-Host": JUDGE0_API_HOST,
        "Content-Type": "application/json",
    }


def run_code(source_code: str, stdin: str, time_limit_sec: int = 2) -> dict:
    """Send one program + input to Judge0, wait, and return the result dict."""
    payload = {
        "source_code": source_code,
        "language_id": PYTHON_LANGUAGE_ID,
        "stdin": stdin,
        "cpu_time_limit": time_limit_sec,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=true",
            json=payload,
            headers=_headers(),
        )
    resp.raise_for_status()
    return resp.json()