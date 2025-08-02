import logging
from datetime import datetime
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd

from phototracks.collection import FileCollection

local_timezone = ZoneInfo("Europe/Madrid")
logger = logging.getLogger(__name__)


class Track(Path):
    def __init__(self, path: Path):
        super().__init__(path)
        try:
            # Use the proper approach for selecting columns in geopandas
            self.gdf = gpd.read_file(path, layer="track_points")
            if self.gdf.empty:
                raise ValueError(f"No track points found in {path}")
            # Filter to only keep the time column after reading
            if "time" in self.gdf.columns:
                self.gdf = self.gdf[["time", "geometry"]]
                self.gdf["time"] = pd.to_datetime(self.gdf["time"])
            else:
                raise ValueError(f"No time column found in {path}")
        except Exception as e:
            raise ValueError(f"Cannot read gpx data from {path}") from e

    @cached_property
    def time_range(self) -> tuple[datetime, datetime]:
        """
        Return the time range of the track.

        Returns:
            tuple[datetime, datetime]: The time range of the track.
        """
        # Filter out any rows with null time values
        # Convert to pandas Series first to ensure notna is available
        time_series = pd.Series(self.gdf["time"])
        valid_times = self.gdf[time_series.notna()]["time"]

        if len(valid_times) == 0:
            raise ValueError("No valid time data found in track points")

        # Get min and max timestamps and explicitly convert to Python datetime objects
        min_time_pd = valid_times.min()
        max_time_pd = valid_times.max()

        # Convert pandas Timestamp to Python datetime
        min_time = datetime.fromtimestamp(
            min_time_pd.timestamp(), tz=min_time_pd.tzinfo
        )
        max_time = datetime.fromtimestamp(
            max_time_pd.timestamp(), tz=max_time_pd.tzinfo
        )

        return (min_time, max_time)


class TrackCollection(FileCollection[Track]):

    def __init__(self, path: Path | str = Path("."), crs: str = "EPSG:4326"):
        super().__init__(Path(path) if isinstance(path, str) else path, ".gpx")
        self.crs = crs

    def _get_path_class(self):
        return Track

    @property
    def gdf(self) -> gpd.GeoDataFrame:
        """
        Return a GeoDataFrame of all tracks in the collection, sorted by time and marked with the source track path in the 'source' column.
        """
        return (
            gpd.GeoDataFrame(
                pd.concat(
                    [
                        (
                            track.gdf.set_crs(self.crs, allow_override=True).assign(
                                track_path=str(track)
                            )
                        )
                        for track in self
                    ],
                    ignore_index=True,
                )
            )
            .sort_values("time")
            .reset_index(drop=True)
        )  # type: ignore[return-value]

    @property
    def gdf_with_time(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            self.gdf[self.gdf["time"].notna()], geometry="geometry", crs=self.crs
        )
