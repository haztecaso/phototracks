from pathlib import Path

from fastapi import FastAPI

app = FastAPI()

tracks_folder = Path("")


@app.get("/tracks")
async def tracks():
    """
    TODO
    """
    ...
