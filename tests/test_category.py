import os
import sys
import pytest
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database

from models.base import ValidationException
from models.category import Category

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass


class TestCategory:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self):
        self.database = models.database.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                Category(
                    id=1,
                    name="Vrac",
                    path="/Vrac/",
                    icon_path="/path/to/icon.jpg",
                ),
                Category(
                    id=2,
                    name="Great",
                    path="/Great/",
                    icon_path="/path/to/great/icon.jpg",
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
        categories = self.database.categories_get()
        assert len(categories) == 2, "There are 2 categories"

        category = self.database.category_get_by_name("Vrac")
        assert type(category) == Category, "There is a single category with name Vrac"

        assert category.path == "Vrac", "The category has the right path"

        assert (
            str(category) == "Vrac @ Vrac"
        ), "The category has the right string representation"

    def test_validations(self):
        category = Category(
            id=1,
            name="Vrac",
            path="/Vrac/",
            icon_path="/path/to/icon.jpg",
        )

        # Test forbidden values
        forbidden_values = {
            "name": ["", None, "a" * 251],
            "path": ["", None, "a" * 251],
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
