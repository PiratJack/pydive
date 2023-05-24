"""A way to convert images between RAW and JPG formats

For example, from RAW to JPG using UFRaw

Classes
----------
ConversionMethod
    A way to convert images from one format to another
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class ConversionMethod(Base):
    """A way to convert images from one format to another

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        Friendly name, for example "darktherapee"
    suffix : str
        The suffix to add to the filename, for example "DT" for darktherapee
    command : str
        A command to execute for the conversion

    Methods
    -------
    validate_* (self, key, value)
        Validator for the corresponding field

    validate_missing_field (self, key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "conversion_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    suffix = Column(String(50), nullable=True)
    command = Column(String(1000), nullable=False)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value)
        if len(value) > 250:
            raise ValidationException(
                _("Max length for conversion method {field} is 250 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("suffix")
    def validate_suffix(self, key, value):
        if len(value) > 50:
            raise ValidationException(
                _("Max length for conversion method {field} is 50 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("command")
    def validate_command(self, key, value):
        self.validate_missing_field(key, value)
        if len(value) > 1000:
            raise ValidationException(
                _("Max length for conversion method {field} is 1000 characters").format(
                    field=key
                ),
                self,
                key,
                value,
            )
        return value

    def validate_missing_field(self, key, value):
        if value == "" or value is None:
            message = _("Missing conversion method {field}").format(field=key)
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        return f"{self.name}"
