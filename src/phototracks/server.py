from datetime import datetime

from fastapi import FastAPI, Path
from pydantic import BaseModel

from .lib import process_track

app = FastAPI()


class TrackMetadata(BaseModel):
    name: str
    start: datetime
    end: datetime


@app.get("/tracks")
async def root():
    return "abc"
