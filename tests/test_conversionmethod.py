import os
import unittest

import pydive.models.database as databasemodel

from pydive.models.base import ValidationException
from pydive.models.conversionmethod import ConversionMethod

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
                ConversionMethod(
                    id=1,
                    name="Darktherapee",
                    suffix="DT",
                    command="darktherapee %SOURCE_FILE% %TARGET_FILE%",
                ),
                ConversionMethod(
                    id=2,
                    name="UFRaw",
                    suffix="ufraw",
                    command="ufraw-cli -s %SOURCE_FILE% -t %TARGET_FILE%",
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
        conversion_methods = self.database.conversionmethods_get()
        self.assertEqual(
            len(conversion_methods),
            2,
            "There are 2 conversion methods",
        )

        conversion_method = self.database.conversionmethods_get_by_suffix("ufraw")
        self.assertEqual(
            type(conversion_method),
            ConversionMethod,
            "There is a single conversion method with suffix ufraw",
        )

        self.assertEqual(
            str(conversion_method),
            "UFRaw",
            "The string representation is correct",
        )

        conversion_method = self.database.conversionmethods_get_by_name("UFRaw")
        self.assertEqual(
            type(conversion_method),
            ConversionMethod,
            "There is a single conversion method with name UFRaw",
        )

    def test_validations(self):
        conversion_method = ConversionMethod(
            id=10,
            name="rawtherapee",
            suffix="RT",
            command="../test.py -s %SOURCE%",
        )

        # Test forbidden values
        forbidden_values = {
            "name": ["", None, "a" * 251],
            "suffix": ["a" * 51],
            "command": ["", None, "a" * 1001],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Conversion methods must have a " + field + " that is not "
                test_name += "None" if value is None else str(value)
                with self.assertRaises(ValidationException) as cm:
                    setattr(conversion_method, field, value)
                self.assertEqual(type(cm.exception), ValidationException, test_name)
                self.assertEqual(
                    cm.exception.item,
                    conversion_method,
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
