"""A storage location is a folder in which pictures are stored

For example, the camera's SD card, a temporary folder or an archive folder

Classes
----------
StorageLocationType
    A type of location: folder or file
StorageLocation
    Folder in which pictures are stored
"""
import gettext
import enum
import sqlalchemy.orm
import os.path

from sqlalchemy import Column, Integer, String, Enum

from .base import Base, ValidationException

_ = gettext.gettext


class StorageLocationType(enum.Enum):
    """Either Folder or File"""

    picture_folder = {
        "name": "picture_folder",
        "file_or_folder": "folder",
    }
    target_scan_folder = {
        "name": "target_scan_folder",
        "file_or_folder": "folder",
    }
    file = {
        "name": "file",
        "file_or_folder": "file",
    }


class StorageLocation(Base):
    """Folder in which pictures are stored

    Attributes
    ----------
    id : int
        Unique ID
    type : StorageLocationType
        The type of location (folder or file)
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
    type = Column(Enum(StorageLocationType, validate_strings=True), nullable=False)
    path = Column(String(250), nullable=False)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value)
        return value

    @sqlalchemy.orm.validates("type")
    def validate_type(self, key, value):
        """Ensure the type field is one of the allowed values"""
        self.validate_missing_field(key, value)
        if isinstance(value, StorageLocationType):
            return value
        if value and isinstance(value, str):
            try:
                return StorageLocationType[value]
            except KeyError as exception:
                raise ValidationException(
                    _("Storage location type is invalid"),
                    self,
                    key,
                    value,
                ) from exception

        raise ValidationException(
            _("Storage location type is invalid"),
            self,
            key,
            value,
        )

    @sqlalchemy.orm.validates("path")
    def validate_path(self, key, value):
        self.validate_missing_field(key, value)
        if self.type:
            if self.type in ("picture_folder", StorageLocationType["picture_folder"]):
                if not value.endswith(os.path.sep):
                    value += os.path.sep

        return value

    def validate_missing_field(self, key, value):
        if value == "" or value is None:
            message = _("Missing storage location {field}").format(field=key)
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        return f"{self.name} @ {self.path}"
