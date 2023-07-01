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

_ = gettext.gettext


class StorageLocationCollision(ValueError):
    """Exception raised when 2 storage location are in one another"""

    def __init__(self, message, path):
        super().__init__(message)
        self.path = path


class Picture:
    """A single picture, corresponding to 1 image file on disk

    Attributes
    ----------
    path : str
        The path to the image file
    trip : str
        The image's trip (leaf folder)
    location : StorageLocation
        The image's storage location
    name : str
        Image file's name (without folder or extension)
    filename : str
        Image file's name (with extension, without folder)

    Methods
    -------
    __init__ (storage_locations, path)
        Stores information based on provided parameters & file path
    """

    def __init__(self, storage_locations, path):
        """Stores information based on provided parameters & file path

        Matches the image to its storage location
        Determines the image's attributes

        Raises StorageLocationCollision if 2 storage locations match the same image

        Parameters
        -------
        storage_locations : list of StorageLocation
            The available storage locations
        path : str
            Image's file path
        """
        self.path = path
        # In which folder / storage location is the picture?
        storage_location = [
            location
            for location in storage_locations
            if path[: len(location.path)] == location.path
        ]
        if len(storage_location) == 1:
            location = storage_location[0]
            self.trip = os.path.dirname(path)[len(location.path) :]
            if self.trip.startswith(os.sep):
                self.trip = self.trip[1:]
            self.location = location
            self.name = os.path.basename(path).rsplit(".", 1)[-2]
            self.filename = os.path.basename(path)
        else:
            raise StorageLocationCollision("recognition failed", path)

    def __repr__(self):
        return (self.name, self.trip, self.location.name, self.path).__repr__()
