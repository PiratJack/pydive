"""SQLAlchemy-based class acting as entry point for most queries

Classes
----------
Database
    Holds different methods for most queries used in the rest of the application
"""
import sqlalchemy

from . import storagelocation
from . import conversionmethod
from . import category

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

    create_tables
        Creates all the DB tables

    storagelocations_get
        Returns a list of all storage locations
    storagelocations_get_picture_folders
        Returns a list of all picture folder storage locations
    storagelocations_get_target_scan_folder
        Returns the folder where to store divelog scan splitted image
    storagelocations_get_divelog
        Returns the storage location for dive log
    storagelocation_get_by_id (storagelocation_id)
        Returns a storage location based on its ID
    storagelocation_get_by_name (storagelocation_name)
        Returns a storage location based on its name

    conversionmethods_get
        Returns all conversion methods
    conversionmethods_get_by_suffix (suffix)
        Returns a conversion method based on its suffix
    conversionmethods_get_by_name (name)
        Returns a conversion method based on its name

    categories_get
        Returns all categories
    category_get_by_name (name)
        Returns a category based on its name

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

    def storagelocations_get_picture_folders(self):
        """Returns a list of all picture folders"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(
                storagelocation.StorageLocation.type
                == storagelocation.StorageLocationType.picture_folder
            )
            .all()
        )

    def storagelocations_get_target_scan_folder(self):
        """Returns the storage location for divelog scan files"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(
                storagelocation.StorageLocation.type
                == storagelocation.StorageLocationType.target_scan_folder
            )
            .one_or_none()
        )

    def storagelocations_get_divelog(self):
        """Returns the storage location for dive log"""
        return (
            self.session.query(storagelocation.StorageLocation)
            .filter(
                storagelocation.StorageLocation.type
                == storagelocation.StorageLocationType.file
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

    # Categories
    def categories_get(self):
        """Returns a list of all categories"""
        return self.session.query(category.Category).all()

    def category_get_by_name(self, name):
        """Returns a category based on its name"""
        return (
            self.session.query(category.Category)
            .filter(category.Category.name == name)
            .one()
        )

    def delete(self, item):
        self.session.delete(item)
        self.session.commit()
