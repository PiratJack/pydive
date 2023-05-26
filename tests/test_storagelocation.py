import os
import unittest

import pydive.models.database as databasemodel

from pydive.models.base import ValidationException
from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestStorageLocation(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                StorageLocation(
                    id=1, name="Camera", type="folder", path="/.../SD_Card/"
                ),
                StorageLocation(
                    id=2, name="Temporary", type="folder", path="/tmp/Pictures/"
                ),
                StorageLocation(
                    id=3,
                    name="Archive",
                    type=StorageLocationType["folder"],
                    path="/Archives/",
                ),
                StorageLocation(
                    id=4, name="Dive log", type="file", path="/Archives/test.txt"
                ),
            ]
        )
        self.database.session.commit()

    def tearDown(self):
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        # Get all
        storage_locations = self.database.storagelocations_get()
        self.assertEqual(
            len(storage_locations),
            4,
            "There are 4 storage locations",
        )

        storage_locations = self.database.storagelocations_get_folders()
        self.assertEqual(
            len(storage_locations),
            3,
            "There are 3 folder storage locations",
        )

        storage_location = self.database.storagelocation_get_by_id(2)
        self.assertEqual(
            storage_location.id,
            2,
            "There is 1 storage locations with ID = 2",
        )
        self.assertEqual(
            storage_location.type.name,
            "folder",
            "The storage location with ID = 2 has type folder",
        )
        # String representation
        self.assertEqual(
            str(storage_location),
            "Temporary @ /tmp/Pictures/",
            "The Temporary folder is at /tmp/Pictures/",
        )

        storage_location = self.database.storagelocation_get_by_name("Camera")
        self.assertEqual(
            storage_location.id,
            1,
            "There is 1 storage locations with name = Camera and it has ID = 1",
        )
        self.assertEqual(
            storage_location.type.name,
            "folder",
            "The storage location with name = Camera has type folder",
        )
        self.database.delete(storage_location)
        storage_locations = self.database.storagelocations_get()
        self.assertEqual(
            len(storage_locations),
            3,
            "After deletion, there are 3 storage locations left",
        )

    def test_validations(self):
        storage_location = StorageLocation(
            id=45,
            name="USB stick",
            type="folder",
            path="/usb_stick/",
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
                with self.assertRaises(ValidationException) as cm:
                    setattr(storage_location, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    storage_location,
                    test_name + " - exception.item is wrong",
                )
                self.assertEqual(
                    cm.exception.key,
                    field,
                    test_name + " - exception.key is wrong",
                )
                self.assertEqual(
                    cm.exception.invalid_value,
                    value,
                    test_name + " - exception.invalid_value is wrong",
                )
