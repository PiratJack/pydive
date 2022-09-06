"""A storage location is a folder in which pictures are stored

For example, the camera's SD card, a temporary folder or an archive folder

Classes
----------
StorageLocation
    Folder in which pictures are stored
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class StorageLocation(Base):
    """Folder in which pictures are stored

    Attributes
    ----------
    id : int
        Unique ID
    path : str
        The absolute path of the folder
    name : str
        The name that should be displayed in the screens

    Methods
    -------
    validate_* (self, key, value)
        Validator for the corresponding field

    validate_missing_field (self, key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "storage_locations"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    path = Column(String(250), nullable=False)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value)
        return value

    @sqlalchemy.orm.validates("path")
    def validate_path(self, key, value):
        self.validate_missing_field(key, value)
        return value

    def validate_missing_field(self, key, value):
        if value == "" or value is None:
            message = _("Missing storage location {field}").format(field=key)
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        return f"{self.name} @ {self.path}"
