import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from phototracks.app import locate_photos
from phototracks.photo import PhotoCollection
from phototracks.track import TrackCollection


class TestApp:
    @pytest.fixture
    def tracks(self):
        return TrackCollection(Path("./tests/assets"))

    @pytest.fixture
    def photos(self):
        return PhotoCollection(Path("./tests/assets"))

    def test_locate_photos(self, tracks, photos):
        """Test locating photos on a track."""
        waypoints = locate_photos(tracks, photos)

        assert isinstance(waypoints, gpd.GeoDataFrame)
        assert len(waypoints) == 2

        assert all(isinstance(wp, Point) for wp in waypoints.geometry)
        assert "time" in waypoints.columns

    def test_locate_photos_out_of_range(self, tracks):
        """Test locating photos with times outside track range."""

        track_gdf = tracks.gdf
        track_start, track_end = track_gdf["time"].min(), track_gdf["time"].max()

        before_track = track_start - pd.Timedelta(days=1)
        after_track = track_end + pd.Timedelta(days=1)

        mock_photos = MagicMock(spec=PhotoCollection)
        mock_photos.df_with_time = pd.DataFrame(
            {
                "photo_src": [
                    "/mock/path/before_track.jpg",
                    "/mock/path/after_track.jpg",
                ],
                "time": [before_track, after_track],
            }
        )

        waypoints = locate_photos(tracks, mock_photos)

        assert isinstance(waypoints, gpd.GeoDataFrame)
        assert len(waypoints) == 0

    def test_locate_photos_empty_collection(self, tracks):
        """Test locating photos with an empty collection."""
        mock_photos = MagicMock(spec=PhotoCollection)
        # Create DataFrame with empty data using a dictionary to avoid typing issues
        mock_photos.df_with_time = pd.DataFrame({"photo_src": [], "time": []})
        waypoints = locate_photos(tracks, mock_photos)

        assert isinstance(waypoints, gpd.GeoDataFrame)
        assert len(waypoints) == 0
