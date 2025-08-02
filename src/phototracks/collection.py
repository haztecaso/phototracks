import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Generic, Type, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Path)


class FileCollection(Generic[T], ABC):
    def __init__(
        self,
        path: Path,
        filter_extensions: str | list[str] | None = None,
        followlinks: bool = False,
    ):
        self.path = path
        match filter_extensions:
            case None:
                self.filter_extensions = None
            case str():
                self.filter_extensions = [filter_extensions]
            case list():
                self.filter_extensions = filter_extensions
        self.followlinks = followlinks

        self._cache: dict[Path, T | None] = {}
        self._paths: set[Path] = set()
        self._populate_paths()

    def _populate_paths(self):
        """
        Populate the _paths set with the paths of the files in the given folder.
        """
        for root, _, files in os.walk(self.path, followlinks=self.followlinks):
            for file in files:
                if self.filter_extensions is None or any(
                    file.lower().endswith(ext.lower()) for ext in self.filter_extensions
                ):
                    self._paths.add(Path(os.path.join(root, file)))

    @abstractmethod
    def _get_path_class(self) -> Type[T]:
        """
        Return the appropriate class for file paths.
        """
        pass

    def __repr__(self) -> str:
        result = ", ".join(map(lambda p: f'"{p}"', self._paths))
        return f"{self.__class__.__name__}({result})"

    def __iter__(self) -> Generator[T, None, None]:
        """
        Iterator of files with the given extension in the given folder.
        """
        path_class = self._get_path_class()

        for path in self._paths:
            if path not in self._cache:
                try:
                    self._cache[path] = path_class(path)
                except ValueError as e:
                    logger.error(
                        "Cannot create %s from %s: %s", path_class, path, str(e)
                    )
                    self._cache[path] = None
                    continue
            item = self._cache[path]
            if item is not None:
                yield item
