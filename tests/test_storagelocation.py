import os
import sys
import pytest
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.database

from models.base import ValidationException
from models.storagelocation import StorageLocation
from models.storagelocation import StorageLocationType

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestStorageLocation:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self):
        self.database = models.database.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                StorageLocation(
                    id=1,
                    name="Camera",
                    type="picture_folder",
                    path=os.path.join("...", "SD_Card"),
                ),
                StorageLocation(
                    id=2,
                    name="Temporary",
                    type="picture_folder",
                    path=os.path.join("tmp", "Pictures"),
                ),
                StorageLocation(
                    id=3,
                    name="Archive",
                    type=StorageLocationType["picture_folder"],
                    path=os.path.join("", "Archives"),
                ),
                StorageLocation(
                    id=4,
                    name="Dive log",
                    type="file",
                    path=os.path.join("", "Archives", "test.txt"),
                ),
                StorageLocation(
                    id=5,
                    name="Scan split folder",
                    type="target_scan_folder",
                    path=os.path.join("", "Divelog"),
                ),
            ]
        )
        self.database.session.commit()

        yield

        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        # Get all
        storage_locations = self.database.storagelocations_get()
        assert len(storage_locations) == 5, "There are 5 storage locations"

        storage_locations = self.database.storagelocations_get_picture_folders()
        assert len(storage_locations) == 3, "There are 3 folder storage locations"

        storage_locations = self.database.storagelocations_get_divelog()
        assert len(storage_locations) == 1, "There is 1 file storage locations"

        storage_locations = self.database.storagelocations_get_target_scan_folder()
        assert storage_locations is not None, "There is 1 target scan folder locations"

        storage_location = self.database.storagelocation_get_by_id(2)
        assert storage_location.id == 2, "There is 1 storage locations with ID = 2"
        assert (
            storage_location.type.name == "picture_folder"
        ), "The storage location with ID = 2 has type picture_folder"
        # String representation
        assert str(storage_location) == "Temporary @ " + os.path.join(
            "tmp", "Pictures", ""
        ), "The Temporary folder is at /tmp/Pictures/"

        storage_location = self.database.storagelocation_get_by_name("Camera")
        assert (
            storage_location.id == 1
        ), "There is 1 storage locations with name = Camera and it has ID = 1"
        assert (
            storage_location.type.name == "picture_folder"
        ), "The storage location with name = Camera has type picture_folder"
        self.database.delete(storage_location)
        storage_locations = self.database.storagelocations_get()
        assert (
            len(storage_locations) == 4
        ), "After deletion, there are 4 storage locations left"

    def test_validations(self):
        storage_location = StorageLocation(
            id=45,
            name="USB stick",
            type="picture_folder",
            path="usb_stick",
        )

        # Test forbidden values
        forbidden_values = {
            "name": ["", None],
            "type": ["", None, "guigh", 27],
            "path": ["", None],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Storage location must have a " + field + " that is not "
                test_name += "None" if value is None else str(value)
                with pytest.raises(ValidationException) as exc_info:
                    setattr(storage_location, field, value)
                exception = exc_info.value
                assert type(exception) == ValidationException, test_name
                assert exception.item == storage_location, (
                    test_name + " - exception.item is wrong"
                )
                assert exception.key == field, test_name + " - exception.key is wrong"
                assert exception.invalid_value == value, (
                    test_name + " - exception.invalid_value is wrong"
                )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
