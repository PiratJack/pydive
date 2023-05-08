import os
import gettext

_ = gettext.gettext


class Picture:
    def __init__(self, folders, path):
        self.path = path
        folder = [
            (type, folders[type])
            for type in folders
            if path[: len(folders[type])] == folders[type]
        ]
        if len(folder) == 1:
            location_type, folder = folder[0]
            self.trip = os.path.dirname(path)[len(folder) :]
            self.location_type = location_type
            self.main_name = os.path.split(path)[-1]
        else:
            print("recognition failed", path)

    def __repr__(self):
        return (self.main_name, self.trip, self.location_type, self.path).__repr__()
