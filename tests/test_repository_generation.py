import os
import unittest
import datetime
import logging
from PyQt5 import QtCore
import zipfile

import pydive.models.database as databasemodel

from pydive.models.conversionmethod import ConversionMethod
from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType
from pydive.models.repository import Repository

logging.basicConfig(level=logging.CRITICAL)

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

BASE_FOLDER = (
    os.path.join("test_images" + str(int(datetime.datetime.now().timestamp())))
    + os.path.sep
)

# This requires actual image files, which are heavy & take time to process
# Hence the separate test class
class TestRepositoryGeneration(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(BASE_FOLDER)
        except OSError:
            pass
        self.all_folders = [
            os.path.join(BASE_FOLDER),
            os.path.join(BASE_FOLDER, "DCIM", ""),
            os.path.join(BASE_FOLDER, "DCIM", "122_12"),
            os.path.join(BASE_FOLDER, "DCIM", "123__05"),
            os.path.join(BASE_FOLDER, "Temporary", ""),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", ""),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", ""),
            os.path.join(BASE_FOLDER, "Temporary", "Korea", ""),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", ""),
            os.path.join(BASE_FOLDER, "Archive", ""),
            os.path.join(BASE_FOLDER, "Archive", "Malta", ""),
            os.path.join(BASE_FOLDER, "Archive", "Korea", ""),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", ""),
            os.path.join(BASE_FOLDER, "Archive_outside_DB", ""),
            os.path.join(BASE_FOLDER, "Archive_outside_DB", "Egypt", ""),
        ]

        self.all_files = [
            os.path.join(BASE_FOLDER, "DCIM", "122_12", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "122_12", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "123__05", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "123__05", "IMG020.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "IMG050.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG010_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG011_convert.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Korea", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Korea", "IMG030_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_convert.jpg"),
            os.path.join(BASE_FOLDER, "Archive_outside_DB", "Egypt", "IMG037.CR2"),
        ]
        with zipfile.ZipFile("test_photos.zip", "r") as zip_ref:
            zip_ref.extractall(".")
            os.rename("test_photos", BASE_FOLDER)

        try:
            os.remove(DATABASE_FILE)
        except OSError:
            pass
        self.database = databasemodel.Database(DATABASE_FILE)
        self.database.session.add_all(
            [
                # Test with final "/" in path
                StorageLocation(
                    id=1,
                    name="Camera",
                    type="folder",
                    path=os.path.join(BASE_FOLDER, "DCIM", ""),
                ),
                # Test without final "/" in path
                StorageLocation(
                    id=2,
                    name="Temporary",
                    type="folder",
                    path=os.path.join(BASE_FOLDER, "Temporary"),
                ),
                StorageLocation(
                    id=3,
                    name="Archive",
                    type=StorageLocationType["folder"],
                    path=os.path.join(BASE_FOLDER, "Archive"),
                ),
                StorageLocation(
                    id=4,
                    name="Inexistant",
                    type="folder",
                    path=os.path.join(BASE_FOLDER, "Inexistant"),
                ),
                StorageLocation(
                    id=5,
                    name="No picture here",
                    type="folder",
                    path=os.path.join(BASE_FOLDER, "Empty"),
                ),
                StorageLocation(
                    id=6,
                    name="Dive log",
                    type="file",
                    path=os.path.join(BASE_FOLDER, "Archives", "test.txt"),
                ),
                ConversionMethod(
                    id=1,
                    name="DarkTherapee",
                    suffix="DT",
                    command="../pydive_generate_picture.py %SOURCE_FILE% -t %TARGET_FOLDER% -c DT > /dev/null",
                ),
                ConversionMethod(
                    id=2,
                    name="RawTherapee",
                    suffix="RT",
                    command="../pydive_generate_picture.py %SOURCE_FILE% -t %TARGET_FOLDER% -c RT > /dev/null",
                ),
            ]
        )
        self.database.session.commit()

        # Load the pictures
        self.locations = self.database.storagelocations_get_folders()
        self.repository = Repository()
        self.repository.load_pictures(self.locations)

    def tearDown(self):
        # Delete database
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

        # Delete folders
        for test_file in self.all_files:
            if os.path.exists(test_file):
                os.remove(test_file)
        for folder in sorted(self.all_folders, reverse=True):
            if os.path.exists(folder):
                os.rmdir(folder)

    def helper_check_paths(self, test, should_exist=[], should_not_exist=[]):
        QtCore.QThreadPool.globalInstance().waitForDone()
        # Add "should exist" to "all_files" so they get deleted later
        self.all_files += should_exist
        self.all_files = list(set(self.all_files))

        # We check all files: both existing and non-existing
        all_files_checked = set(self.all_files + should_not_exist)
        should_exist = [f for f in self.all_files if f not in should_not_exist]
        for path in all_files_checked:
            if path in should_exist:
                self.assertTrue(os.path.exists(path), f"{test} - File {path}")
            else:
                self.assertFalse(os.path.exists(path), f"{test} - File {path}")

    # List of Repository.generate_pictures tests - "KO" denotes when a ValueError is raised
    #  picture_group   source_location    trip
    #       X                 X             X      test_repository_generate_pictures_all_parameters_multiple_methods
    #       X                 X             X      test_repository_generate_pictures_all_parameters_single_method

    #       X                 X                    test_repository_generate_pictures_missing_trip
    #       X                               X      test_repository_generate_pictures_missing_source_location
    #                         X             X      test_repository_generate_pictures_missing_picture_group

    #       X                                      test_repository_generate_pictures_picture_group
    #                         X                    test_repository_generate_pictures_source_location
    #                                       X      test_repository_generate_pictures_trip
    def test_repository_generate_pictures_all_parameters_multiple_methods(self):
        test = "Picture generate: all parameters provided (multiple methods)"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get()
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG041"]

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_DT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_generate_pictures_all_parameters_single_method(self):
        test = "Picture generate: all parameters provided (only DT)"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG041"]

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_generate_pictures_missing_trip(self):
        test = "Picture generate: missing trip"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG041"]

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_generate_pictures_missing_source_location(self):
        test = "Picture generate: missing source location"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = None
        trip = "Malta"
        picture_group = self.repository.trips["Malta"]["IMG001"]

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_generate_pictures_missing_picture_group(self):
        test = "Picture generate: missing picture group"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041_convert.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041_DT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_generate_pictures_picture_group(self):
        test = "Picture generate: only picture_group provided"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = None
        trip = None
        picture_group = self.repository.trips["Malta"]["IMG001"]

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_generate_pictures_source_location(self):
        test = "Picture generate: only source_location provided"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None

        with self.assertRaises(ValueError) as cm:
            self.repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip or picture_group must be provided",
                test,
            )

        self.helper_check_paths(test)

    def test_repository_generate_pictures_trip(self):
        test = "Picture generate: only trip provided"
        target_location = self.database.storagelocation_get_by_name("Archive")
        conversion_methods = self.database.conversionmethods_get_by_suffix("DT")
        source_location = None
        trip = "Malta"
        picture_group = None

        self.repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_DT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_DT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)
