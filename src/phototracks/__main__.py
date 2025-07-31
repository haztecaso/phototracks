import itertools
import os
from pathlib import Path

import click

from .lib import (
    add_track_waypoints,
    create_thumbnail,
    get_files_with_extension,
    get_image_date,
    process_track,
)

OptionPath = click.Path(
    exists=True,
    file_okay=False,
    dir_okay=True,
    readable=True,
    resolve_path=True,
    path_type=Path,
)


@click.command()
@click.option("-t", "--tracks-folder", default=Path("./tracks"), type=OptionPath)
@click.option("-i", "--images-folder", default=Path("./images"), type=OptionPath)
@click.option("-o", "--output-folder", default=Path("./out"), type=OptionPath)
def main(tracks_folder: Path, images_folder: Path, output_folder: Path):
    track_files = get_files_with_extension(tracks_folder, ".gpx")
    track_data = list(map(process_track, track_files))
    track_data.sort(key=lambda x: x.start)

    image_files = get_files_with_extension(images_folder, ".NEF")
    image_data = list(map(get_image_date, image_files))
    image_data.sort(key=lambda x: x.time)

    for image, track in itertools.product(image_data, track_data):
        if track.start <= image.time <= track.end:
            track.images.append(image)

    os.makedirs(output_folder, exist_ok=True)

    for track in filter(lambda track: len(track.images) > 0, track_data):
        add_track_waypoints(track)
        folder = output_folder / track.path.stem
        os.makedirs(folder, exist_ok=True)
        track.gpx.to_file(folder / f"{track.path.stem}.gpx")
        for image in track.images:
            create_thumbnail(image, folder)
