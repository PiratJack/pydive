import os
import gettext

import models.picture

_ = gettext.gettext


class Repository:
    folders = {}
    pictures = []
    raw_extensions = [".cr2"]
    processed_extensions = [".jpg", ".jpeg"]

    def __init__(self, folders=None):
        if folders:
            self.folders = folders.copy()
            self.load_pictures()

    def load_pictures(self, folders=None):
        pictures = []
        if folders:
            self.folders |= folders.copy()
        for folder in self.folders:
            pictures += self.read_folder([], folder, self.folders[folder])
        self.pictures = pictures

    def read_folder(self, pictures, path_type, path):
        if not os.path.isdir(path):
            return None
        for element in os.listdir(path):
            full_path = os.path.join(path, element)
            if os.path.isdir(full_path):
                self.read_folder(pictures, path_type, full_path)
            else:
                matching_extension = [
                    ext
                    for ext in self.raw_extensions
                    if full_path.lower().endswith(ext)
                ]
                if matching_extension:
                    pictures.append(models.picture.Picture(self.folders, full_path))
        return pictures

    def __getattr__(self, attr):
        if attr == "trips":
            trips = {}
            for picture in self.pictures:
                if picture.trip not in trips:
                    trips[picture.trip] = []
                trips[picture.trip].append(picture)
            return trips
