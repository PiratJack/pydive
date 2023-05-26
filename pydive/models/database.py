"""SQLAlchemy-based class acting as entry point for most queries

Classes
----------
Database
    Holds different methods for most queries used in the rest of the application
"""
import sqlalchemy

from . import storagelocation
from . import conversionmethod

from .base import Base


class Database:
    """Point of entry class for queries into the database

    Attributes
    ----------
    engine : sqlalchemy.Engine
        The database engine
    metadata : sqlalchemy.MetaData
        SQLAlchemy medatada object
    session : sqlalchemy.orm.Session
        Database session

    Methods
    -------
    __init__ (self, database_file)
        Loads (or creates) the database from the provided file

    create_tables (self)
        Creates all the DB tables

    storagelocations_get (self)
        Returns a list of all storage locations
    storagelocation_get_by_id (self, storagelocation_id)
        Returns a storage location based on its ID

    delete (self, item)
        Deletes the provided item
    """

    def __init__(self, database_file):
        """Loads (or creates) the database from the provided file"""
        self.engine = sqlalchemy.create_engine("sqlite:///" + database_file)
        self.metadata = sqlalchemy.MetaData()
        self.create_tables()

        self.session = sqlalchemy.orm.sessionmaker(bind=self.engine)()

    def create_tables(self):
        """Creates all the DB tables"""
        Base.metadata.create_all(self.engine)

    # Storage locations
    def storagelocations_get(self):
        """Returns a list of all storage locations"""
        return self.session.query(storagelocation.StorageLocation).all()

    def storagelocations_get_folders(self):
        """Returns a list of all folder storage locations"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(
                storagelocation.StorageLocation.type
                == storagelocation.StorageLocationType.folder
            )
            .all()
        )

    def storagelocation_get_by_id(self, storagelocation_id):
        """Returns a storage location based on its ID"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(storagelocation.StorageLocation.id == storagelocation_id)
            .one()
        )

    def storagelocation_get_by_name(self, storagelocation_name):
        """Returns a storage location based on its name"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(storagelocation.StorageLocation.name == storagelocation_name)
            .one()
        )

    # Conversion methods
    def conversionmethods_get(self):
        """Returns a list of all conversion methods"""
        return self.session.query(conversionmethod.ConversionMethod).all()

    def conversionmethods_get_by_suffix(self, suffix):
        """Returns a conversion method based on its suffix"""
        return (
            self.session.query(conversionmethod.ConversionMethod)
            .filter(conversionmethod.ConversionMethod.suffix == suffix)
            .one()
        )

    def conversionmethods_get_by_name(self, name):
        """Returns a conversion method based on its name"""
        return (
            self.session.query(conversionmethod.ConversionMethod)
            .filter(conversionmethod.ConversionMethod.name == name)
            .one()
        )

    def delete(self, item):
        self.session.delete(item)
        self.session.commit()
