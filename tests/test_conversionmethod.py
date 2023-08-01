import os
import sys
import pytest
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database as databasemodel

from models.base import ValidationException
from models.conversionmethod import ConversionMethod

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestStorageLocation:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self):
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

        yield

        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

    def test_gets(self):
        # Get all
        conversion_methods = self.database.conversionmethods_get()
        assert len(conversion_methods) == 2, "There are 2 conversion methods"

        conversion_method = self.database.conversionmethods_get_by_suffix("ufraw")
        assert (
            type(conversion_method) == ConversionMethod
        ), "There is a single conversion method with suffix ufraw"

        assert str(conversion_method) == "UFRaw", "The string representation is correct"

        conversion_method = self.database.conversionmethods_get_by_name("UFRaw")
        assert (
            type(conversion_method) == ConversionMethod
        ), "There is a single conversion method with name UFRaw"

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
                with pytest.raises(ValidationException) as cm:
                    setattr(conversion_method, field, value)
                exception = cm.value
                assert type(exception) == ValidationException, test_name
                assert exception.item == conversion_method, (
                    test_name + " - exception.item is wrong"
                )
                assert exception.key == field, test_name + " - exception.key is wrong"
                assert exception.invalid_value == value, (
                    test_name + " - exception.invalid_value is wrong"
                )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
