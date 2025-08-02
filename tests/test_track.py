import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pytest

from phototracks.track import Track, TrackCollection


class TestTrack:
    @pytest.fixture
    def sample_gpx_file(self):
        """Return the path to a sample GPX file from the assets directory."""
        # Use the existing GPX file from the assets directory
        return Path("./tests/assets/RK_gpx_2025-01-26_1029.gpx")

    def test_init(self, sample_gpx_file):
        """Test Track initialization with a valid GPX file."""
        track = Track(sample_gpx_file)

        assert track == sample_gpx_file
        assert isinstance(track.gdf, gpd.GeoDataFrame)
        assert not track.gdf.empty
        assert "time" in track.gdf.columns
        assert "geometry" in track.gdf.columns

    def test_init_invalid_file(self, tmp_path):
        """Test Track initialization with an invalid file."""
        invalid_path = tmp_path / "invalid.gpx"
        invalid_path.touch()  # Create empty file

        with pytest.raises(ValueError, match="Cannot read gpx data"):
            Track(invalid_path)

    def test_time_range(self, sample_gpx_file):
        """Test the time_range property."""
        track = Track(sample_gpx_file)
        start_time, end_time = track.time_range

        assert isinstance(start_time, datetime)
        assert isinstance(end_time, datetime)
        assert start_time < end_time
        assert start_time.tzinfo is not None  # Check timezone is set


class TestTrackCollection:

    @pytest.fixture
    def temp_collection_dir(self, assets_dir):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            assets_dir = Path("./tests/assets")
            for asset in assets_dir.glob("*"):
                shutil.copy(asset, temp_path / asset.name)

            yield temp_path
