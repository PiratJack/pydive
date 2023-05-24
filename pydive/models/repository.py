import os
import gettext

from .picture import Picture as PictureModel
from .picturegroup import PictureGroup

_ = gettext.gettext


class Repository:
    allowed_extensions = [".cr2", ".jpg", ".jpeg"]

    def __init__(self, storage_locations=None):
        self.storage_locations = {}
        self.pictures = []
        self.picture_groups = []

        if storage_locations:
            self.storage_locations = storage_locations.copy()
            self.load_pictures()

    def load_pictures(self, storage_locations=None):
        # Find all pictures
        pictures = []
        if storage_locations:
            self.storage_locations |= storage_locations.copy()
            self.pictures = []
            self.picture_groups = []
        for name in self.storage_locations:
            new_pictures = self.read_folder([], name, self.storage_locations[name])
            if new_pictures:
                pictures += new_pictures
        self.pictures = pictures

        # Then group them
        picture_names = set(picture.name for picture in self.pictures)
        picture_names = sorted(picture_names)
        for picture_name in picture_names:
            matching_groups = [
                group
                for group in self.picture_groups
                if picture_name.startswith(group.name)
            ]
            pictures = [
                picture for picture in self.pictures if picture.name == picture_name
            ]

            if len(matching_groups) == 0:
                group = PictureGroup(picture_name)
                self.picture_groups.append(group)
            else:
                # There should not be multiple matching groups
                # This is because groups are created in alphabetical order
                # Therefore groups with shorter names are processed first
                group = matching_groups[0]
            for picture in pictures:
                group.add_picture(picture)

    def read_folder(self, pictures, location_name, path):
        if not os.path.isdir(path):
            return None
        for element in os.listdir(path):
            full_path = os.path.join(path, element)
            if os.path.isdir(full_path):
                self.read_folder(pictures, location_name, full_path)
            else:
                matching_extension = [
                    ext
                    for ext in self.allowed_extensions
                    if full_path.lower().endswith(ext)
                ]
                if matching_extension:
                    pictures.append(PictureModel(self.storage_locations, full_path))
        return pictures

    def add_picture(self, picture_group, location, path):
        picture = PictureModel({location.name: location.path}, path)
        picture_group.add_picture(picture)

    def __getattr__(self, attr):
        if attr == "trips":
            trips = {}
            for picture_group in self.picture_groups:
                if picture_group.trip not in trips:
                    trips[picture_group.trip] = {}
                trips[picture_group.trip][picture_group.name] = picture_group
            return trips
