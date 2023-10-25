import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.database

from models.base import ValidationException
from models.storagelocation import StorageLocation
from models.storagelocation import StorageLocationType


class TestStorageLocation:
    def test_gets(self, pydive_db):
        # Get all
        storage_locations = pydive_db.storagelocations_get()
        assert len(storage_locations) == 7, "There are 7 storage locations"

        storage_locations = pydive_db.storagelocations_get_picture_folders()
        assert len(storage_locations) == 5, "There are 5 folder storage locations"

        storage_locations = pydive_db.storagelocations_get_divelog()
        assert len(storage_locations) == 1, "There is 1 dive log locations"

        storage_locations = pydive_db.storagelocations_get_target_scan_folder()
        assert storage_locations is not None, "There is 1 target scan folder locations"

        storage_location = pydive_db.storagelocation_get_by_id(2)
        assert storage_location.id == 2, "There is 1 storage locations with ID = 2"
        assert (
            storage_location.type.name == "picture_folder"
        ), "The storage location with ID = 2 has type picture_folder"
        # String representation
        assert str(storage_location) == "Temporary @ " + os.path.join(
            pytest.BASE_FOLDER, "Temporary", ""
        ), "The Temporary folder is at /tmp/Pictures/"

        storage_location = pydive_db.storagelocation_get_by_name("Camera")
        assert (
            storage_location.id == 1
        ), "There is 1 storage locations with name = Camera and it has ID = 1"
        assert (
            storage_location.type.name == "picture_folder"
        ), "The storage location with name = Camera has type picture_folder"
        pydive_db.delete(storage_location)
        storage_locations = pydive_db.storagelocations_get()
        assert (
            len(storage_locations) == 6
        ), "After deletion, there are 6 storage locations left"

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
