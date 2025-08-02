import itertools
import os
from pathlib import Path

import click

from phototracks.app import locate_photos, save_waypoints
from phototracks.photo import PhotoCollection
from phototracks.track import TrackCollection

OptionPath = click.Path(
    exists=True,
    file_okay=False,
    dir_okay=True,
    readable=True,
    resolve_path=True,
    path_type=Path,
)


@click.command()
@click.option("-t", "--tracks-folder", default=Path("."), type=OptionPath)
@click.option("-i", "--images-folder", default=Path("."), type=OptionPath)
@click.option("-o", "--output", default=Path("waypoints.geojson"), type=Path)
def main(tracks_folder: Path, images_folder: Path, output: Path):
    photos = PhotoCollection(images_folder)
    tracks = TrackCollection(tracks_folder)
    located_photos = locate_photos(tracks, photos)
    save_waypoints(located_photos, output)
