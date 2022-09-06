import os
import unittest

import pydive.models.database as databasemodel

from pydive.models.base import ValidationException
from pydive.models.storagelocation import StorageLocation

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestSharePrice(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                StorageLocation(id=1, name="Camera", path="/.../SD_Card/"),
                StorageLocation(id=2, name="Temporary", path="/tmp/Pictures/"),
                StorageLocation(id=3, name="Archive", path="/Archives/"),
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
            3,
            "There are 3 storage locations",
        )

        storage_location = self.database.storagelocation_get_by_id(2)
        self.assertEqual(
            storage_location.id,
            2,
            "There is 1 storage locations with ID = 2",
        )
        # String representation
        self.assertEqual(
            str(storage_location),
            "Temporary @ /tmp/Pictures/",
            "The Temporary folder is at /tmp/Pictures/",
        )

        self.database.delete(storage_location)
        storage_locations = self.database.storagelocations_get()
        self.assertEqual(
            len(storage_locations),
            2,
            "After deletion, there are 2 storage locations left",
        )

    def test_validations(self):
        storage_location = StorageLocation(
            id=4,
            name="USB stick",
            path="/usb_stick/",
        )

        # Test forbidden values
        forbidden_values = {
            "name": ["", None],
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
