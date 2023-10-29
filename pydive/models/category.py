"""A category is a subfolder in which pictures are stored, with an icon to display it

Classes
----------
Category
    Subfolder in which pictures are stored
"""
import gettext
import sqlalchemy.orm
import os.path

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class Category(Base):
    """Subfolder in which pictures are stored

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        The name that should be displayed in the screens
    relative_path : str
        The relative path of the category
    icon : str
        The icon to display for this category

    Methods
    -------
    validate_* (self, key, value)
        Validator for the corresponding field

    validate_missing_field (self, key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    relative_path = Column(String(250), nullable=False)
    icon = Column(String(250), nullable=True)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value)
        if len(value) > 250:
            raise ValidationException(
                _("Max length for category {field} is 250 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("relative_path")
    def validate_type(self, key, value):
        self.validate_missing_field(key, value)
        value = value.strip(os.path.sep)
        if len(value) > 250:
            raise ValidationException(
                _("Max length for category {field} is 250 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("icon")
    def validate_path(self, key, value):
        if value and len(value) > 250:
            raise ValidationException(
                _("Max length for category {field} is 250 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    def validate_missing_field(self, key, value):
        if value == "" or value is None:
            message = _("Missing category {field}").format(field=key)
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        return f"{self.name} @ {self.relative_path}"
