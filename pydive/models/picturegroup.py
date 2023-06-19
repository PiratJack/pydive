import os
import gettext
from PyQt5 import QtCore

from .picture import Picture as PictureModel

_ = gettext.gettext
# TODO: PictureGroup > add documentation


class PictureGroup(QtCore.QObject):
    pictureAdded = QtCore.pyqtSignal(PictureModel, str)
    pictureRemoved = QtCore.pyqtSignal(str, str)

    def __init__(self, group_name):
        super().__init__()
        self.name = group_name
        self.trip = None
        self.pictures = {}  # Structure is conversion_type: picture model
        self.locations = {}

    def add_picture(self, picture):
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
        self.locations[picture.location_name] = self.locations.get(
            picture.location_name, []
        ) + [picture]

        self.pictureAdded.emit(picture, conversion_type)

    def remove_picture(self, picture):
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

        os.unlink(picture.path)

        # Update locations
        self.locations[picture.location_name].remove(picture)
        if not self.locations[picture.location_name]:
            del self.locations[picture.location_name]

        self.pictureRemoved.emit(conversion_type, picture.location_name)

        del picture

    def __repr__(self):
        nb_pictures = sum([len(p) for p in self.pictures.values()])
        return (self.name, self.trip, str(nb_pictures) + " pictures").__repr__()
