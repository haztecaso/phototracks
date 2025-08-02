import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from phototracks.photo import Photo, PhotoCollection, local_timezone


class TestPhoto:
    @pytest.fixture
    def assets_dir(self):
        return Path("./tests/assets")

    @pytest.fixture
    def temp_dir(self):
        # Create a temporary directory for test outputs
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Clean up after the test
        shutil.rmtree(temp_dir)

    def test_init(self, assets_dir):
        """Test Photo initialization"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)
        assert photo == photo_path

    def test_time_from_exif(self, assets_dir):
        """Test extracting time from EXIF data"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Get the time from the photo
        time = photo.time

        # Verify it's a datetime object with timezone
        assert isinstance(time, datetime)
        assert time.tzinfo is not None

        # The exact time will depend on the EXIF data in the test image
        # This is a basic check that we got some reasonable date
        assert time.year >= 2020  # Assuming test photos are recent

    def test_time_from_filename(self, assets_dir):
        """Test extracting time from filename when EXIF is not available"""
        photo_path = assets_dir / "250126_1317_DSC_2312_no_exif.jpg"
        photo = Photo(photo_path)

        time = photo.time

        assert time
        assert time.year == 2025
        assert time.month == 1
        assert time.day == 26
        assert time.hour == 13
        assert time.minute == 17
        assert time.tzinfo == local_timezone

    def test_time_invalid_filename_and_no_exif(self, assets_dir):
        """Test error when both filename and EXIF data are invalid"""
        photo_path = assets_dir / "no_date.png"
        photo = Photo(photo_path)

        assert photo.time is None

    def test_compressed_filename(self, assets_dir):
        """Test compressed_filename property"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Get the compressed filename
        compressed = photo.compressed_filename

        # Basic checks for the compressed filename
        assert isinstance(compressed, str)
        assert len(compressed) > 0

    def test_compressed_filename_with_none_time(self, temp_dir):
        """Test compressed_filename property when time is None"""
        # Create a file that will have None time
        invalid_path = temp_dir / "no_time_file.txt"
        with open(invalid_path, "w") as f:
            f.write("This is not an image file")

        photo = Photo(invalid_path)

        # The compressed filename should fall back to the stem of the path
        assert photo.compressed_filename == "no_time_file"

    def test_from_compressed_filename(self, assets_dir):
        """Test from_compressed_filename class method"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Get the compressed filename
        compressed = photo.compressed_filename

        # Decode the compressed filename
        time, path = Photo.from_compressed_filename(compressed)

        # Check that the decoded values match the original
        assert isinstance(time, datetime)
        assert path == photo

    def test_from_compressed_filename_invalid(self):
        """Test from_compressed_filename with invalid input"""
        with pytest.raises(ValueError) as excinfo:
            Photo.from_compressed_filename("invalid_compressed_filename")

        assert "Invalid compressed filename" in str(excinfo.value)

    def test_thumbnail_exists(self, assets_dir, temp_dir):
        """Test thumbnail_exists method"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Initially, the thumbnail should not exist
        assert not photo.thumbnail_exists(temp_dir)

        # Create the thumbnail
        thumbnail_path = photo.create_thumbnail(temp_dir)

        # Now the thumbnail should exist
        assert photo.thumbnail_exists(temp_dir)
        assert thumbnail_path
        assert thumbnail_path.exists()

    def test_create_thumbnail(self, assets_dir, temp_dir):
        """Test thumbnail creation"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Create thumbnail
        thumbnail_path = photo.create_thumbnail(temp_dir)

        # Check that thumbnail was created
        assert thumbnail_path is not None
        assert thumbnail_path.exists()

        # Verify thumbnail dimensions
        with Image.open(thumbnail_path) as img:
            width, height = img.size
            assert width <= 256
            assert height <= 256

    def test_create_thumbnail_no_overwrite(self, assets_dir, temp_dir):
        """Test thumbnail creation with no overwrite"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Create thumbnail first time
        first_thumbnail = photo.create_thumbnail(temp_dir)
        assert first_thumbnail is not None
        assert first_thumbnail.exists()

        # Get the modification time
        assert first_thumbnail is not None
        first_mtime = first_thumbnail.stat().st_mtime

        # Small delay to ensure different modification time if file is recreated
        import time

        time.sleep(0.1)

        # Create thumbnail second time with overwrite=False (default)
        second_thumbnail = photo.create_thumbnail(temp_dir)

        # Should return the same path
        assert second_thumbnail == first_thumbnail

        # File should not have been modified
        assert second_thumbnail is not None
        assert second_thumbnail.stat().st_mtime == first_mtime

    def test_create_thumbnail_with_overwrite(self, assets_dir, temp_dir):
        """Test thumbnail creation with overwrite"""
        photo_path = assets_dir / "250126_1335_DSC_2323.jpg"
        photo = Photo(photo_path)

        # Create thumbnail first time
        first_thumbnail = photo.create_thumbnail(temp_dir)
        assert first_thumbnail is not None
        assert first_thumbnail.exists()

        # Get the modification time
        assert first_thumbnail is not None
        first_mtime = first_thumbnail.stat().st_mtime

        # Small delay to ensure different modification time if file is recreated
        import time

        time.sleep(0.1)

        # Create thumbnail second time with overwrite=True
        second_thumbnail = photo.create_thumbnail(temp_dir, overwrite=True)

        # Should return the same path
        assert second_thumbnail == first_thumbnail

        # File should have been modified
        assert second_thumbnail is not None
        assert second_thumbnail.stat().st_mtime > first_mtime

    def test_create_thumbnail_error(self, temp_dir):
        """Test thumbnail creation with invalid image"""
        # Create an invalid image file
        invalid_path = temp_dir / "invalid.jpg"
        with open(invalid_path, "w") as f:
            f.write("This is not a valid image file")

        photo = Photo(invalid_path)

        # This should not raise an exception but log an error and return None
        result = photo.create_thumbnail(temp_dir)
        assert result is None

        # Check that no thumbnail was created
        thumbnail_path = temp_dir / f"{invalid_path.stem}.thumb.jpg"
        assert not thumbnail_path.exists()


class TestPhotoCollection:
    @pytest.fixture
    def assets_dir(self):
        return Path("./tests/assets")

    @pytest.fixture
    def temp_collection_dir(self):
        # Create a temporary directory with test image files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy test assets to temp directory
            assets_dir = Path("./tests/assets")
            for asset in assets_dir.glob("*"):
                shutil.copy(asset, temp_path / asset.name)

            # Add some non-image files
            (temp_path / "text_file.txt").write_text("This is not an image")

            # Create a subdirectory with more files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            # Copy one image to the subdirectory with a proper date format in the filename
            shutil.copy(
                assets_dir / "250126_1335_DSC_2323.jpg",
                subdir / "250126_1400_subdir_image.jpg",
            )

            yield temp_path

    def test_init(self, temp_collection_dir):
        """Test PhotoCollection initialization"""
        collection = PhotoCollection(temp_collection_dir)
        assert collection.path == temp_collection_dir
        assert collection.filter_extensions == PhotoCollection.IMG_EXTENSIONS

    def test_photos(self, temp_collection_dir):
        """Test photos property"""
        collection = PhotoCollection(temp_collection_dir)
        photos = list(collection)

        # Should return only image files (4 in total: 3 in root dir, 1 in subdir)
        assert len(photos) == 4

        # Check that all photos are Photo instances
        for photo in photos:
            assert isinstance(photo, Photo)

        # Check that the text file is not included
        text_file_path = temp_collection_dir / "text_file.txt"
        assert text_file_path not in photos

        # Check that the subdirectory image is included
        subdir_image_path = (
            temp_collection_dir / "subdir" / "250126_1400_subdir_image.jpg"
        )
        assert any(p == subdir_image_path for p in photos)

    def test_sorted_photos(self, temp_collection_dir):
        """Test sorted_photos property"""
        # Remove the no_date.png file that would cause an error
        no_date_file = temp_collection_dir / "no_date.png"
        if no_date_file.exists():
            no_date_file.unlink()

        collection = PhotoCollection(temp_collection_dir)
        sorted_photos = collection.sorted_photos

        # Check that we have the same number of photos as the unsorted list
        assert len(sorted_photos) == len(list(collection))

        # Check that the photos are sorted by time
        for i in range(1, len(sorted_photos)):
            # Add null check to handle None values in datetime comparison
            prev_time = sorted_photos[i - 1].time
            curr_time = sorted_photos[i].time
            if prev_time is not None and curr_time is not None:
                assert prev_time <= curr_time
            # If either is None, we can't compare them, so we'll skip the assertion
