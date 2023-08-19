"""A group of images that belong together, based on their file name

Classes
----------
PictureGroup
    A group of images that belong together, based on their file name
"""
import gettext
import logging
from PyQt5 import QtCore

from .picture import Picture as PictureModel
from .storagelocation import StorageLocation

_ = gettext.gettext
logger = logging.getLogger(__name__)


class PictureGroup(QtCore.QObject):
    """A group of images that belong together, based on their file name

    The images may be in different folders or different types (RAW, jpg, ...)
    They are matched together if their filenames start with the same elements

    Attributes
    ----------
    pictureAdded : pyqtSignal
        Emitted with a new image is added
    pictureRemoved : pyqtSignal
        Emitted with an image is deleted
    name : str
        The name of the picture group (= the common part of the pictures' file names)
    trip : str
        The trip of the picture group (= shared trip across all images)
    pictures : dict of form conversion_type: picture
        The pictures belonging to this group, organized by conversion type
    locations : dict of form location.name: picture
        The pictures belonging to this group, organized by location

    Methods
    -------
    __init__
        Initializes values to defaults
    add_picture (picture)
        Adds a new picture to the group, after checking that it matches the group
    remove_picture (picture)
        Removes a picture from the group, after checking that it matches the group
    """

    pictureAdded = QtCore.pyqtSignal(PictureModel, str)
    pictureRemoved = QtCore.pyqtSignal(str, StorageLocation)
    pictureGroupDeleted = QtCore.pyqtSignal(str, str)
    pictureTasksDone = QtCore.pyqtSignal()
    pictureTasksStart = QtCore.pyqtSignal()

    def __init__(self, group_name):
        """Initializes values to defaults

        Parameters
        -------
        group_name : str
            The name of the picture group
        """
        logger.debug(f"PictureGroup.init {group_name}")
        super().__init__()
        self.name = group_name
        self.trip = None
        self.pictures = {}  # Structure is conversion_type: picture model
        self.locations = {}
        self.tasks = []

    def add_picture(self, picture):
        """Adds a new picture to the group, after checking that it matches the group

        Determines the image's conversion type
        May recalculate all images' conversion types if the new image is a RAW one

        Raises ValueError if the picture's trip or name do not match the group
        Emits pictureAdded once done

        Parameters
        -------
        picture : Picture
            The picture to add
        """
        logger.debug(
            f"PictureGroup.add_picture: {picture.filename} to {self.name} during {self.trip}"
        )
        # Check trip matches the group's trip
        if not self.trip:
            self.trip = picture.trip
        if picture.trip and picture.trip != self.trip:
            raise ValueError(
                "Picture " + picture.name + " has the wrong trip for group " + self.name
            )

        # The picture name starts with the group name ==> easy
        conversion_type = ""
        if picture.name.startswith(self.name):
            conversion_type = picture.name.replace(self.name, "")
            if conversion_type.startswith("_"):
                conversion_type = conversion_type[1:]
            if conversion_type not in self.pictures:
                self.pictures[conversion_type] = []
            self.pictures[conversion_type].append(picture)
        # Otherwise we have to re-convert all images
        elif self.name.startswith(picture.name):
            prefix_to_add = self.name[len(picture.name) :]
            if prefix_to_add.startswith("_"):
                prefix_to_add = prefix_to_add[1:]
            self.name = picture.name
            self.pictures = {
                prefix_to_add + conversion_type: self.pictures[conversion_type]
                for conversion_type in self.pictures
            }
            self.pictures[""] = [picture]
        else:
            raise ValueError(
                "Picture " + picture.name + " does not belong to group " + self.name
            )

        # Update locations
        self.locations[picture.location.name] = self.locations.get(
            picture.location.name, []
        ) + [picture]

        logger.debug(
            f"PictureGroup.add_picture: emit pictureAdded: {picture.filename} to {self.name} during {self.trip}"
        )
        self.pictureAdded.emit(picture, conversion_type)

    def remove_picture(self, picture):
        """Removes a picture from the group, after checking that it matches the group

        Deletes the actual image file

        Raises ValueError if the picture's trip do not match the group
        Emits pictureRemoved once done

        Parameters
        -------
        picture : Picture
            The picture to remove
        """
        logger.debug(
            f"PictureGroup.remove_picture: {picture.filename} from {self.name} during {self.trip}"
        )
        # Check trip matches the group's trip
        if picture.trip and picture.trip != self.trip:
            raise ValueError(
                "Picture " + picture.name + " has the wrong trip for group " + self.name
            )

        # The picture name starts with the group name ==> easy
        conversion_type = picture.name.replace(self.name, "")
        if conversion_type.startswith("_"):
            conversion_type = conversion_type[1:]
        self.pictures[conversion_type].remove(picture)
        if not self.pictures[conversion_type]:
            del self.pictures[conversion_type]

        # Update locations
        self.locations[picture.location.name].remove(picture)
        if not self.locations[picture.location.name]:
            del self.locations[picture.location.name]

        logger.debug(
            f"PictureGroup.remove_picture: emit pictureRemoved: {picture.filename} from {self.name} during {self.trip}"
        )
        self.pictureRemoved.emit(conversion_type, picture.location)
        del picture

        if not self.pictures and not self.tasks:
            logger.debug(
                f"PictureGroup.remove_picture: emit pictureGroupDeleted for {self.name} during {self.trip}"
            )
            self.pictureGroupDeleted.emit(self.trip, self.name)

    def add_task(self, process):
        logger.debug(
            f"PictureGroup.add_task {process} for {self.name} during {self.trip}"
        )
        self.tasks.append(process)
        self.pictureTasksStart.emit()
        process.signals.taskFinished.connect(lambda: self.task_done(process))

    def task_done(self, process):
        logger.debug(
            f"PictureGroup.task_done {process} for {self.name} during {self.trip}"
        )
        self.tasks.remove(process)
        if not self.tasks:
            logger.debug(
                f"PictureGroup.task_done: emit pictureTasksDone for {self.name} during {self.trip}"
            )
            self.pictureTasksDone.emit()

    def __repr__(self):
        nb_pictures = sum([len(p) for p in self.pictures.values()])
        return (self.name, self.trip, str(nb_pictures) + " pictures").__repr__()
