import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from phototracks.photo import Photo, PhotoCollection
from phototracks.track import Track, TrackCollection

logger = logging.getLogger(__name__)


def locate_photos(tracks: TrackCollection, photos: PhotoCollection) -> gpd.GeoDataFrame:
    """
    Locate the given photos by matching their timestamps to the tracks.
    Returns a GeoDataFrame with the photos locations.

    Args:
        tracks: Track collection to match photos to.
        photos: Photo collection to get locations for.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing the photos locations.
    """

    df_photos = photos.df_with_time
    df_tracks = tracks.gdf_with_time

    df_photos["time"] = pd.to_datetime(df_photos["time"], utc=True).astype(
        "datetime64[ms, UTC]"
    )
    df_tracks["time"] = pd.to_datetime(df_tracks["time"], utc=True).astype(
        "datetime64[ms, UTC]"
    )

    merged_df = pd.merge_asof(
        df_photos,
        df_tracks,
        on="time",
        direction="nearest",
    )

    return gpd.GeoDataFrame(merged_df, geometry="geometry", crs=tracks.gdf.crs)


def save_waypoints(gdf: gpd.GeoDataFrame, path: Path) -> None:
    """
    Save the waypoints to a GeoJSON file.

    Args:
        gdf: GeoDataFrame containing the waypoints.
        path: Path to save the waypoints to.
    """
    gdf["time"] = gdf["time"].dt.tz_localize(None).astype(str)
    gdf.to_file(path, driver="GeoJSON")
