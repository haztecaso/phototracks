import tempfile
from pathlib import Path
from typing import Type

import pytest

from phototracks.collection import FileCollection


# Create a concrete subclass of FileCollection for testing
class TestPathCollection(FileCollection[Path]):
    def _get_path_class(self) -> Type[Path]:
        return Path


class TestFileCollection:
    @pytest.fixture
    def temp_dir(self):
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files with different extensions
            (temp_path / "file1.txt").write_text("test content")
            (temp_path / "file2.jpg").write_text("test image")
            (temp_path / "file3.JPG").write_text("test image uppercase")
            (temp_path / "file4.png").write_text("test png")

            # Create a subdirectory with more files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "subfile1.txt").write_text("test subdir content")
            (subdir / "subfile2.jpg").write_text("test subdir image")

            yield temp_path

    def test_init(self, temp_dir):
        """Test FileCollection initialization"""
        collection = TestPathCollection(temp_dir)
        assert collection.path == temp_dir
        assert collection.filter_extensions is None

        collection_with_filter = TestPathCollection(temp_dir, ".jpg")
        assert collection_with_filter.path == temp_dir
        assert collection_with_filter.filter_extensions == [".jpg"]

        collection_with_list_filter = TestPathCollection(temp_dir, [".jpg", ".png"])
        assert collection_with_list_filter.path == temp_dir
        assert collection_with_list_filter.filter_extensions == [".jpg", ".png"]

    def test_files_no_filter(self, temp_dir):
        """Test files property with no extension filter"""
        collection = TestPathCollection(temp_dir)
        files = list(collection)

        # Should return all 6 files (4 in root dir, 2 in subdir)
        assert len(files) == 6

        # Check that all expected files are in the result
        filenames = [f.name for f in files]
        assert "file1.txt" in filenames
        assert "file2.jpg" in filenames
        assert "file3.JPG" in filenames
        assert "file4.png" in filenames
        assert "subfile1.txt" in filenames
        assert "subfile2.jpg" in filenames

    def test_files_string_filter(self, temp_dir):
        """Test files property with string extension filter"""
        collection = TestPathCollection(temp_dir, ".jpg")
        files = list(collection)

        # Should return only the 3 jpg files (2 in root dir, 1 in subdir)
        assert len(files) == 3

        # Check that only jpg files are in the result
        filenames = [f.name for f in files]
        assert "file1.txt" not in filenames
        assert "file2.jpg" in filenames
        assert "file3.JPG" in filenames  # Case insensitive
        assert "file4.png" not in filenames
        assert "subfile1.txt" not in filenames
        assert "subfile2.jpg" in filenames

    def test_files_list_filter(self, temp_dir):
        """Test files property with list extension filter"""
        collection = TestPathCollection(temp_dir, [".jpg", ".png"])
        files = list(collection)

        # Should return only the 4 jpg/png files (3 in root dir, 1 in subdir)
        assert len(files) == 4

        # Check that only jpg and png files are in the result
        filenames = [f.name for f in files]
        assert "file1.txt" not in filenames
        assert "file2.jpg" in filenames
        assert "file3.JPG" in filenames  # Case insensitive
        assert "file4.png" in filenames
        assert "subfile1.txt" not in filenames
        assert "subfile2.jpg" in filenames
