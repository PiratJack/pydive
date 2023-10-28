import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

from models.base import ValidationException
from models.category import Category


class TestCategory:
    def test_gets(self, pydive_db):
        # Get all
        categories = pydive_db.categories_get()
        assert len(categories) == 2, "There are 2 categories"

        # Get one and check its attributes
        category = pydive_db.category_get_by_name("Top")
        assert type(category) == Category, "There is a single category with name Top"
        assert category.relative_path == "Sélection", "The category has the right path"
        assert (
            str(category) == "Top @ Sélection"
        ), "The category has the right string representation"

    def test_validations(self):
        category = Category(
            id=3,
            name="New_item",
            relative_path="/New_item/",
            icon_path="/path/to/icon.jpg",
        )

        # Test forbidden values
        forbidden_values = {
            "name": ["", None, "a" * 251],
            "relative_path": ["", None, "a" * 251],
            "icon_path": ["a" * 251],
        }

        for field in forbidden_values:
            for value in forbidden_values[field]:
                test_name = "Categories must have a " + field + " that is not "
                test_name += "None" if value is None else str(value)
                with pytest.raises(ValidationException) as cm:
                    setattr(category, field, value)
                exception = cm.value
                assert type(exception) == ValidationException, test_name
                assert exception.item == category, (
                    test_name + " - exception.item is wrong"
                )
                assert exception.key == field, test_name + " - exception.key is wrong"
                assert exception.invalid_value == value, (
                    test_name + " - exception.invalid_value is wrong"
                )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
