"""Represents a single image file with some additional information

Classes
----------
StorageLocationCollision
    Exception raised with a storage location is within another

Picture
    A single picture, corresponding to 1 image file on disk
"""
import os
import gettext
import logging

_ = gettext.gettext
logger = logging.getLogger(__name__)


class StorageLocationCollision(ValueError):
    """Exception raised when 2 storage location are in one another"""

    def __init__(self, message, path):
        super().__init__(message)
        self.path = path


class Picture:
    """A single picture, corresponding to 1 image file on disk

    The file path is considered to be composed as such:
    - Location path
    - Trip (can span multiple folders)
    - Category (may be absent)

    Attributes
    ----------
    path : str
        The path to the image file
    trip : str
        The image's trip (leaf folder)
    location : StorageLocation
        The image's storage location
    category : str
        The category of the image (subfolder)
    name : str
        Image file's name (without folder or extension)
    filename : str
        Image file's name (with extension, without folder)

    Methods
    -------
    __init__ (storage_locations, categories, path)
        Stores information based on provided parameters & file path
    """

    def __init__(self, storage_locations, categories, path):
        """Stores information based on provided parameters & file path

        Matches the image to its storage location
        Determines the image's attributes

        Raises StorageLocationCollision if 2 storage locations match the same image

        Parameters
        -------
        storage_locations : list of StorageLocation
            The available storage locations
        categories : list of Category
            The available categories
        path : str
            Image's file path
        """
        logger.debug(f"Picture.init: {storage_locations}, {categories}, {path}")
        self.path = path
        # In which folder / storage location is the picture?
        storage_location = [
            location
            for location in storage_locations
            if path[: len(location.path)] == location.path
        ]
        if len(storage_location) == 1:
            location = storage_location[0]
            self.trip = os.path.dirname(path)[len(location.path) :].strip(os.path.sep)
            self.category = ""
            matching_categories = [c for c in categories if self.trip.endswith(c.path)]
            if matching_categories:
                if len(matching_categories) != 1:
                    logger.warning(
                        f"Picture recognition failed: found categories {', '.join([c.name for c in matching_categories])} for {path}"
                    )
                    raise StorageLocationCollision("recognition failed", path)
                self.category = matching_categories[0]
                self.trip = self.trip.removesuffix(self.category.path).strip(
                    os.path.sep
                )
            self.location = location
            self.name = os.path.basename(path).rsplit(".", 1)[-2]  # Remove extension
            self.filename = os.path.basename(path)
        else:
            logger.warning(
                f"Picture recognition failed: found matches {', '.join([s.name for s in storage_location])} for {path} - Searched in {', '.join([s.name for s in storage_locations])}"
            )
            raise StorageLocationCollision("recognition failed", path)

    def __repr__(self):
        return " ".join(
            [
                self.name,
                "in",
                self.location.name,
                "during",
                self.trip,
                "- path",
                self.path,
            ]
        )
