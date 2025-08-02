import gzip
import json
import logging
from base64 import b64decode, b64encode
from datetime import datetime
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

import exifread
import pandas as pd
from exifread.core.exceptions import ExifNotFound, InvalidExif
from PIL import Image

from .collection import FileCollection

# TODO: Improve timezone handling
local_timezone = ZoneInfo("Europe/Madrid")

logger = logging.getLogger(__name__)


class Photo(Path):
    @cached_property
    def time(self) -> datetime | None:
        """
        Return the time of the image.
        It will try to get the time from the exif data.
        If it fails, it will try to get the time from the filename.

        Returns:
            datetime: The time of the image.
        """
        with open(self, "rb") as f:
            try:
                dt_raw = exifread.process_file(f)["Image DateTime"]
                dt = datetime.strptime(str(dt_raw), "%Y:%m:%d %H:%M:%S")
            except (KeyError, ExifNotFound, InvalidExif):
                dt = datetime.now(local_timezone)
                try:
                    basename = self.stem.split("_")
                    dt_raw = f"{basename[0]}_{basename[1]}"
                    dt = datetime.strptime(dt_raw, "%y%m%d_%H%M")
                except (ValueError, IndexError):
                    logger.debug("Could not get time from %s.", self)
                    return None
        return dt.replace(tzinfo=local_timezone)

    @property
    def compressed_filename(self) -> str:
        """
        Return the compressed filename of the image.
        """
        if self.time is None:
            # Use the filename as fallback if time is not available
            return self.stem

        data = {"time": self.time.strftime("%Y%m%d_%H%M%S"), "path": str(self)}
        json_bytes = json.dumps(data).encode("utf-8")
        compressed = gzip.compress(json_bytes)
        return b64encode(compressed).decode("utf-8")

    @classmethod
    def from_compressed_filename(
        cls, compressed_filename: str
    ) -> tuple[datetime, Path]:
        """
        Create a Photo instance from a compressed filename.

        Args:
            compressed_filename: The compressed filename to decode.

        Returns:
            A tuple containing the datetime and path of the photo.

        Raises:
            ValueError: If the compressed filename is not valid.
        """
        try:
            compressed_bytes = b64decode(compressed_filename)
            decompressed = gzip.decompress(compressed_bytes)
            data = json.loads(decompressed.decode("utf-8"))
            return datetime.strptime(data["time"], "%Y%m%d_%H%M%S").replace(
                tzinfo=local_timezone
            ), Path(data["path"])
        except Exception as e:
            raise ValueError(f"Invalid compressed filename: {e}")

    def thumbnail_exists(self, path: Path) -> bool:
        """
        Check if the thumbnail exists.

        Args:
            path: Path where the thumbnail will be saved.

        Returns:
            bool: True if the thumbnail exists, False otherwise.
        """
        # Use a simpler filename format to avoid path length issues
        return (path / f"{self.stem}.thumb.jpg").exists()

    def create_thumbnail(self, path: Path, overwrite: bool = False) -> Path | None:
        """
        Create a thumbnail for the image.

        Args:
            path: Path where the thumbnail will be saved.
            overwrite: Whether to overwrite the thumbnail if it already exists.

        Returns:
            Path: Path to the thumbnail or None if the thumbnail could not be created.
        """
        # Use a simpler filename format to avoid path length issues
        thumbnail_path = path / f"{self.stem}.thumb.jpg"

        if thumbnail_path.exists() and not overwrite:
            return thumbnail_path

        try:
            # Ensure the parent directory exists
            path.mkdir(parents=True, exist_ok=True)

            with Image.open(self) as im:
                im.thumbnail((256, 256))
                # TODO: Avoid filename collisions
                im.save(thumbnail_path, "JPEG")
                logger.info("Created thumbnail %s", thumbnail_path)
                return thumbnail_path
        except OSError as e:
            logger.error("Cannot create thumbnail for %s: %s", self, str(e))
            return None


class PhotoCollection(FileCollection[Photo]):
    # TODO: Make configurable
    IMG_EXTENSIONS = [
        ".bmp",
        ".gif",
        ".heic",
        ".heif",
        ".jpeg",
        ".jpg",
        ".nef",
        ".png",
        ".raw",
        ".tiff",
        ".webp",
    ]

    def __init__(
        self, path: Path = Path("."), followlinks: bool = False, relative: bool = True
    ):
        super().__init__(
            Path(path) if isinstance(path, str) else path,
            self.IMG_EXTENSIONS,
            followlinks,
        )
        self.relative = relative

    def _get_path_class(self):
        """
        Return the Photo class for file paths.
        """
        return Photo

    @property
    def sorted_photos(self) -> list[Photo]:
        """
        List of photos sorted by time, excluding photos without a valid time.
        """
        return sorted(
            filter(lambda photo: photo.time is not None, self),
            key=lambda photo: photo.time,  # type: ignore
        )

    @property
    def df(self) -> pd.DataFrame:
        data = ((p.resolve() if not self.relative else str(p), p.time) for p in self)
        # Use a dict to create the DataFrame with properly typed columns
        df = pd.DataFrame(data=[(src, t) for src, t in data], columns=["photo_src", "time"])  # type: ignore
        return df.sort_values("time")

    @property
    def df_with_time(self) -> pd.DataFrame:
        return self.df[self.df["time"].notna()]  # type: ignore

    @property
    def df_without_time(self) -> pd.DataFrame:
        return self.df[self.df["time"].isna()]  # type: ignore
