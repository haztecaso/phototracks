#!/usr/bin/env python3

import os, logging
from pathlib import Path
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo
from dataclasses import dataclass

import click
import exifread
from gpx.gpx import GPX

local_timezone = ZoneInfo("Europe/Madrid")

def get_files_with_extension(folder:Path, extension:str) -> Iterable[Path]:
    for path, contents, folder_files in os.walk(folder):
        if len(contents) == 0:
            for file in folder_files:
                if file.endswith(extension):
                    yield Path(path) / file

@dataclass
class ImageData():
    path: Path
    time: datetime

@dataclass
class TrackData():
    path: Path
    gpx: GPX
    start: datetime
    end: datetime
    images: list[ImageData]

def process_track(path:Path) -> TrackData:
    gpx = GPX.from_file(path)
    assert len(gpx.tracks) == 1, "File with more than one track"
    assert len(gpx.tracks[0].segments) == 1, "Track with more than one segment"
    segment = gpx.tracks[0].segments[0]
    start = min(point.time.astimezone(local_timezone) for point in segment.points if point.time is not None)
    end =  max(point.time.astimezone(local_timezone) for point in segment.points if point.time is not None)
    return TrackData(path, gpx, start, end, [])

def add_track_waypoints(track:TrackData):
    assert len(track.gpx.tracks) == 1, "File with more than one track"
    assert len(track.gpx.tracks[0].segments) == 1, "Track with more than one segment"
    if len(track.images) == 0:
        return
    segment = track.gpx.tracks[0].segments[0]
    for image in track.images:
        wp = min(segment.points, key=lambda x: abs(x.time - image.time) if x.time is not None else 999999)
        wp.name = str(image.path.stem)
        wp.cmt = str(image.path)
        track.gpx.waypoints.append(wp)
    new_file  = track.path.parent / (track.path.stem + "_with_imgs.gpx")
    track.gpx.to_file(new_file)


def get_image_date(path: Path) -> ImageData:
    dt = datetime.now()
    try:
        basename = path.stem.split("_")
        dt_raw = f"{basename[0]}_{basename[1]}"
        dt = datetime.strptime(dt_raw, "%y%m%d_%H%M")
    except ValueError:
        logging.warning(f"{path} has invalid filename. Reading datetime from exif.")
        with open(path, 'rb') as f:
            raw_datetime = exifread.process_file(f)["Image DateTime"]
            dt = datetime.strptime(str(raw_datetime), "%Y:%m:%d %H:%M:%S", )
    finally:
        return ImageData(path, dt.replace(tzinfo=local_timezone))


@click.command()
@click.option('-t', '--tracks-folder', default=Path("./tracks"), 
                                                       type=click.Path(exists=True,
                                                       file_okay=False,
                                                       dir_okay=True,
                                                       readable=True, 
                                                       resolve_path=True,
                                                       path_type=Path)
              )
@click.option('-i', '--images-folder', default=Path("./images"),
                                                       type=click.Path(exists=True,
                                                       file_okay=False,
                                                       dir_okay=True,
                                                       readable=True, 
                                                       resolve_path=True,
                                                       path_type=Path
                                                       )
              )

def main(tracks_folder:Path, images_folder:Path):
    track_files = get_files_with_extension(tracks_folder, ".gpx")
    image_files = get_files_with_extension(images_folder, ".NEF")

    track_data = list(map(process_track, track_files))
    image_data = list(map(get_image_date, image_files))

    track_data.sort(key=lambda x: x.start)
    image_data.sort(key=lambda x: x.time)

    for image in image_data:
        for track in track_data:
            if track.start <= image.time <= track.end:
                track.images.append(image)

    for track in track_data:
        add_track_waypoints(track)


if __name__ == '__main__':
    main()
