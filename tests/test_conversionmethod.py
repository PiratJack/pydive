import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

from models.base import ValidationException
from models.conversionmethod import ConversionMethod


class TestStorageLocation:
    def test_gets(self, pydive_db):
        # Get all
        conversion_methods = pydive_db.conversionmethods_get()
        assert len(conversion_methods) == 2, "There are 2 conversion methods"

        conversion_method = pydive_db.conversionmethods_get_by_id(1)
        assert (
            type(conversion_method) == ConversionMethod
        ), "There is a single conversion method with ID 1"

        conversion_method = pydive_db.conversionmethods_get_by_suffix("RT")
        assert (
            type(conversion_method) == ConversionMethod
        ), "There is a single conversion method with suffix RT"

        assert (
            str(conversion_method) == "RawTherapee"
        ), "The string representation is correct"

        conversion_method = pydive_db.conversionmethods_get_by_name("RawTherapee")
        assert (
            type(conversion_method) == ConversionMethod
        ), "There is a single conversion method with name RawTherapee"

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
