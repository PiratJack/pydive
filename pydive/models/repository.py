import os
import gettext

import models.picture

_ = gettext.gettext


class Repository:
    storage_locations = {}
    pictures = []
    raw_extensions = [".cr2"]
    processed_extensions = [".jpg", ".jpeg"]

    def __init__(self, storage_locations=None):
        if storage_locations:
            self.storage_locations = storage_locations.copy()
            self.load_pictures()

    def load_pictures(self, storage_locations=None):
        pictures = []
        if storage_locations:
            self.storage_locations |= storage_locations.copy()
        for name in self.storage_locations:
            pictures += self.read_folder([], name, self.storage_locations[name])
        self.pictures = pictures

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
                    for ext in self.raw_extensions
                    if full_path.lower().endswith(ext)
                ]
                if matching_extension:
                    pictures.append(
                        models.picture.Picture(self.storage_locations, full_path)
                    )
        return pictures

    def __getattr__(self, attr):
        if attr == "trips":
            trips = {}
            for picture in self.pictures:
                if picture.trip not in trips:
                    trips[picture.trip] = []
                trips[picture.trip].append(picture)
            return trips
