"""Various classes used in models

Classes
----------
ValidationException
    The provided data doesn't match requirements (such as mandatory fields)
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ValidationException(Exception):
    """The provided data doesn't match requirements (such as mandatory fields)"""

    def __init__(self, message, item, key, invalid_value):
        super().__init__(message)
        self.message = message
        self.item = item
        self.key = key
        self.invalid_value = invalid_value
