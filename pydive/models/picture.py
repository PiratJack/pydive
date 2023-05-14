import os
import gettext

_ = gettext.gettext


class Picture:
    def __init__(self, storage_locations, path):
        self.path = path
        # In which folder / storage location is the picture?
        storage_location = [
            (name, storage_locations[name])
            for name in storage_locations
            if path[: len(storage_locations[name])] == storage_locations[name]
        ]
        if len(storage_location) == 1:
            location_name, location_path = storage_location[0]
            self.trip = os.path.dirname(path)[len(location_name) + 1 :]
            self.location_name = location_name
            self.main_name = os.path.split(path)[-1]
        else:
            print("recognition failed", path)

    def __repr__(self):
        return (self.main_name, self.trip, self.location_name, self.path).__repr__()
