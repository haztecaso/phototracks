#!/usr/bin/env python3

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import exifread
from gpx.gpx import GPX
from PIL import Image
from pydantic import BaseModel, ConfigDict

local_timezone = ZoneInfo("Europe/Madrid")


def get_files_with_extension(folder: Path, extension: str) -> Iterable[Path]:
    for path, contents, folder_files in os.walk(folder):
        if len(contents) == 0:
            for file in folder_files:
                if file.endswith(extension):
                    yield Path(path) / file


class ImageData(BaseModel):
    path: Path
    time: datetime


class TrackData(BaseModel):
    path: Path
    gpx: GPX
    start: datetime
    end: datetime
    images: list[ImageData]

    model_config = ConfigDict(arbitrary_types_allowed=True)


def process_track(path: Path) -> TrackData:
    gpx = GPX.from_file(path)
    assert len(gpx.tracks) == 1, "File with more than one track"
    assert len(gpx.tracks[0].segments) == 1, "Track with more than one segment"
    segment = gpx.tracks[0].segments[0]
    start = min(
        point.time.astimezone(local_timezone)
        for point in segment.points
        if point.time is not None
    )
    end = max(
        point.time.astimezone(local_timezone)
        for point in segment.points
        if point.time is not None
    )
    return TrackData(path=path, gpx=gpx, start=start, end=end, images=[])


def add_track_waypoints(track: TrackData):
    assert len(track.gpx.tracks) == 1, "File with more than one track"
    assert len(track.gpx.tracks[0].segments) == 1, "Track with more than one segment"
    if len(track.images) == 0:
        return
    segment = track.gpx.tracks[0].segments[0]
    for image in track.images:
        wp = min(
            segment.points,
            key=lambda x: abs(x.time - image.time) if x.time is not None else 999999,
        )
        wp.name = str(image.path.stem)
        wp.cmt = str(image.path)
        track.gpx.waypoints.append(wp)


def create_thumbnail(image: ImageData, output_folder: Path):
    try:
        with Image.open(image.path) as im:
            im.thumbnail((256, 256))
            im.save(output_folder / f"{image.path.stem}.thumb.jpg", "JPEG")
    except OSError as e:
        print("Cannot create thumbnail for", image.path, e)


def get_image_date(path: Path) -> ImageData:
    # TODO: Parametrize date format and timezone
    dt = datetime.now()
    try:
        basename = path.stem.split("_")
        dt_raw = f"{basename[0]}_{basename[1]}"
        dt = datetime.strptime(dt_raw, "%y%m%d_%H%M")
    except ValueError:
        logging.warning(f"{path} has invalid filename. Reading datetime from exif.")
        with open(path, "rb") as f:
            raw_datetime = exifread.process_file(f)["Image DateTime"]
            dt = datetime.strptime(
                str(raw_datetime),
                "%Y:%m:%d %H:%M:%S",
            )
    finally:
        return ImageData(path=path, time=dt.replace(tzinfo=local_timezone))
