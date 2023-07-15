import os
import unittest
import datetime
import logging
from PyQt5 import QtCore, QtTest

import pydive.models.database as databasemodel

from pydive.models.conversionmethod import ConversionMethod
from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType
from pydive.models.repository import Repository
from pydive.models.picture import Picture, StorageLocationCollision

logging.basicConfig(level=logging.CRITICAL)

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

BASE_FOLDER = (
    os.path.join("test_images" + str(int(datetime.datetime.now().timestamp())))
    + os.path.sep
)


class TestRepository(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(BASE_FOLDER)
        except OSError:
            pass
        self.all_folders = [
            os.path.join(BASE_FOLDER),
            os.path.join(BASE_FOLDER, "DCIM", ""),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", ""),
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
            os.path.join(BASE_FOLDER, "Empty", ""),
        ]
        for folder in self.all_folders:
            os.makedirs(folder, exist_ok=True)
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
        for test_file in self.all_files:
            open(test_file, "w").close()

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
            os.rmdir(folder)

    def test_load_pictures_trip_recognition(self):
        # Check if recognition worked
        test = "Load pictures: Count trips"
        self.assertEqual(len(self.repository.trips), 5, test)

        test = "Load pictures: Count pictures with no trips"
        self.assertEqual(len(self.repository.trips[""]), 4, test)

        test = "Load pictures: Count pictures in a given trip"
        self.assertEqual(len(self.repository.trips["Malta"]), 2, test)

    def test_string_representation(self):
        test = "String representation: picture group"
        picture_group = self.repository.trips["Malta"]["IMG001"]
        self.assertEqual(str(picture_group), "('IMG001', 'Malta', '3 pictures')", test)

        picture = [
            p
            for p in picture_group.pictures[""]
            if p.path.endswith(os.path.join("Temporary", "Malta", "IMG001.CR2"))
        ]
        picture = picture[0]

        test = "String representation: picture"
        self.assertEqual(
            str(picture),
            "IMG001 in Temporary during Malta - path "
            + os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001.CR2")
            + "",
            test,
        )

        test = "String representation: picture.filename"
        self.assertEqual(picture.filename, "IMG001.CR2", test)

    def test_load_pictures_storage_location_collision(self):
        test = "Load pictures: storage location collision"
        with self.assertRaises(StorageLocationCollision, msg=test):
            new_location = StorageLocation(
                id=999,
                name="Used path",
                type="folder",
                path=os.path.join(BASE_FOLDER, "Temporary", "Malta"),
            )
            logger = logging.getLogger("pydive.models.picture")
            logger.setLevel(logging.CRITICAL)
            self.repository.load_pictures([new_location])
            logger.setLevel(logging.WARNING)

    def test_storage_location_add(self):
        test = "Add a storage location: Count trips"
        nb_trips_before = len(self.repository.trips)
        new_location = StorageLocation(
            id=999,
            name="Outside_DB",
            type="folder",
            path=os.path.join(BASE_FOLDER, "Archive_outside_DB"),
        )
        self.repository.load_pictures([new_location])
        self.assertEqual(len(self.repository.trips), nb_trips_before + 1, test)

    def test_storage_location_add_with_collision(self):
        test = "Add a storage location: subfolder of existing folder"
        test_repo = Repository()
        test_repo.load_pictures(self.locations)
        new_location = StorageLocation(
            id=999,
            name="Used path",
            type="folder",
            path=os.path.join(BASE_FOLDER, "Temporary", "Malta"),
        )
        with self.assertRaises(ValueError, msg=test) as cm:
            logger = logging.getLogger("pydive.models.picture")
            logger.setLevel(logging.CRITICAL)
            self.repository.load_pictures([new_location])
            logger.setLevel(logging.WARNING)
            self.assertEqual(type(cm.exception), StorageLocationCollision, test)

    def helper_check_paths(self, test, should_exist=[], should_not_exist=[]):
        QtCore.QThreadPool.globalInstance().waitForDone()
        all_files_checked = (
            [
                os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
                os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
                os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
                os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_convert.CR2"),
                os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG041.CR2"),
                os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040.CR2"),
                os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_RT.jpg"),
                os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_DT.jpg"),
                os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_convert.CR2"),
                os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG041.CR2"),
                os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040.CR2"),
                os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_RT.jpg"),
                os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_DT.jpg"),
                os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_convert.CR2"),
                os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041.CR2"),
            ]
            + should_exist
            + should_not_exist
        )
        all_files_checked = set(all_files_checked)

        initial_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Sweden", "IMG041.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040_convert.jpg"),
        ]

        self.all_files += should_exist
        should_exist += initial_files
        for path in should_not_exist:
            if path in should_exist:
                should_exist.remove(path)
        for path in all_files_checked:
            if path in should_exist:
                self.assertTrue(os.path.exists(path), f"{test} - File {path}")
            else:
                self.assertFalse(os.path.exists(path), f"{test} - File {path}")
        self.all_files = list(set(self.all_files))

    # List of Repository.copy_pictures tests - "KO" denotes when a ValueError is raised
    # source_location   trip    picture_group   conversion_method
    #       X             X             X               X       test_repository_copy_pictures_all_parameters

    #       X             X             X                       test_repository_copy_pictures_missing_conversion_method
    #       X             X                             X       test_repository_copy_pictures_missing_picture_group
    #                     X             X               X       test_repository_copy_pictures_missing_source_location
    #       X                           X               X       test_repository_copy_pictures_missing_trip

    #                                   X               X       test_repository_copy_pictures_conversion_method_and_picture_group
    #       X                                           X       test_repository_copy_pictures_conversion_method_and_source_location KO
    #                     X                             X       test_repository_copy_pictures_conversion_method_and_trip
    #       X                           X                       test_repository_copy_pictures_picture_group_and_source_location
    #                     X             X                       test_repository_copy_pictures_picture_group_and_trip
    #       X             X                                     test_repository_copy_pictures_source_location_and_trip

    #                                                   X       test_repository_copy_pictures_conversion_method KO
    #                                   X                       test_repository_copy_pictures_picture_group
    #       X                                                   test_repository_copy_pictures_source_location KO
    #                     X                                     test_repository_copy_pictures_trip

    def test_repository_process_group_finished_signal(self):
        test = "Picture copy: all parameters provided (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Archive")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG040"]
        conversion_method = ""

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )
        QtCore.QThreadPool.globalInstance().waitForDone()

        expected_signal = QtTest.QSignalSpy(process.finished)
        self.assertTrue(expected_signal.isValid())

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040.CR2"),
        ]
        self.all_files += new_files

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_all_parameters(self):
        test = "Picture copy: all parameters provided (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Archive")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG040"]
        conversion_method = ""

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_conversion_method(self):
        test = "Picture copy: all parameters provided except conversion_method"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG040"]
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_picture_group(self):
        test = "Picture copy: all parameters provided except picture_group (copies some of the trip)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = ""

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_source_location(self):
        test = "Picture copy: all parameters provided except source_location (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG040"]
        conversion_method = ""

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_trip(self):
        # This test gives the same result as "all parameters" since trip will be ignored
        test = "Picture copy: all parameters provided except trip (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method_and_picture_group(self):
        test = "Picture copy: conversion_method and picture_group provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method_and_source_location(self):
        test = "Picture copy: conversion_method and source_location provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None
        conversion_method = ""

        with self.assertRaises(ValueError) as cm:
            self.repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip or picture_group must be provided",
                test,
            )

        self.helper_check_paths(test)

    def test_repository_copy_pictures_conversion_method_and_trip(self):
        test = "Picture copy: conversion_method and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_picture_group_and_source_location(self):
        test = "Picture copy: picture_group and source_location provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_picture_group_and_trip(self):
        test = "Picture copy: picture_group and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_source_location_and_trip(self):
        test = "Picture copy: source_location and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method(self):
        test = "Picture copy: only conversion_method provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = None
        conversion_method = ""

        with self.assertRaises(ValueError) as cm:
            self.repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip or picture_group must be provided",
                test,
            )

        self.helper_check_paths(test)

    def test_repository_copy_pictures_picture_group(self):
        test = "Picture copy: only picture_group provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_source_location(self):
        test = "Picture copy: only source_location provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None
        conversion_method = None

        with self.assertRaises(ValueError) as cm:
            self.repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip or picture_group must be provided",
                test,
            )

        self.helper_check_paths(test)

    def test_repository_copy_pictures_trip(self):
        test = "Picture copy: only trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG041.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_change_trip_pictures(self):
        # Change trip (with actual changes)
        # TODO: test > write this function
        # Need test cases for each situation:
        # source_trip=None or provided, picture_group=None or provided
        pass

    def test_repository_change_trip_pictures_finished(self):
        # Change trip (without actual changes - meant to increase coverage
        # TODO: test > write this function
        # Need test cases for each situation:
        # source_trip=None or provided, picture_group=None or provided
        pass

    def test_repository_remove_pictures_1_picture(self):
        test = "Picture remove: actual deletion of 1 picture"
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        path = picture.path

        process = self.repository.remove_pictures(test, None, picture_group, picture)

        self.assertEqual(str(process), test + " (1 tasks)", test)
        self.helper_check_paths(test, [], [path])

    def test_repository_remove_pictures_trip(self):
        test = "Picture remove: actual deletion of a trip"
        picture_files = [
            p for p in self.all_files if os.path.sep + "Korea" + os.path.sep in p
        ]

        self.repository.remove_pictures(test, trip="Korea")

        self.helper_check_paths(test, [], picture_files)

    def test_repository_remove_pictures_validations(self):
        # Delete image without changing structure of .pictures and .locations
        test = "Remove picture: At least 1 trip/picture reference is required"
        with self.assertRaises(ValueError) as cm:
            self.repository.remove_pictures(test)
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip, picture_group or picture must be provided",
                test,
            )

        test = "Remove picture: picture_group required if picture provided"
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        with self.assertRaises(ValueError) as cm:
            self.repository.remove_pictures(test, picture=picture)
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Either trip, picture_group or picture must be provided",
                test,
            )

    def test_repository_remove_picture_no_structure_change(self):
        # Remove image without deleting the actual files
        # This allows detection by coverage
        test = "Remove picture, keep .pictures and.locations"
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        location_initial_count = len(picture_group.locations["Temporary"])
        conversion_type_initial_count = len(picture_group.pictures[""])
        path = picture.path
        self.repository.remove_picture(picture_group, picture.location, picture.path)
        self.assertTrue(
            os.path.exists(path),
            test + ": file not deleted (on purpose)",
        )
        self.assertEqual(
            len(picture_group.locations["Temporary"]),
            location_initial_count - 1,
            test + ": deletion from picture_group.locations",
        )
        self.assertEqual(
            len(picture_group.pictures[""]),
            conversion_type_initial_count - 1,
            test + ": deletion from picture_group.pictures",
        )

    def test_repository_remove_picture_structure_change(self):
        # Remove image without deleting the actual files
        # This allows detection by coverage
        test = "Remove picture, remove keys from .pictures and.locations"
        picture_group = self.repository.trips["Korea"]["IMG030"]
        picture = picture_group.pictures["RT"][0]
        path = picture.path
        self.repository.remove_picture(picture_group, picture.location, picture.path)
        self.assertTrue(
            os.path.exists(path),
            test + ": file not deleted (on purpose)",
        )
        self.assertNotIn(
            "RT",
            picture_group.pictures,
            test + ": .pictures no longer has RT as key",
        )
        self.assertNotIn(
            "Archive",
            picture_group.locations,
            test + ": .locations no longer has Archive as key",
        )

    def test_picture_group_add_pictures_wrong_name(self):
        test = "Add picture: wrong group name"
        picture_group = self.repository.trips["Malta"]["IMG001"]
        picture = [
            p
            for p in self.repository.trips["Malta"]["IMG002"].pictures[""]
            if p.path.endswith("IMG002.CR2")
        ]

        picture = picture[0]
        with self.assertRaises(ValueError) as cm:
            picture_group.add_picture(picture)
        self.assertEqual(type(cm.exception), ValueError, test)
        self.assertEqual(
            cm.exception.args[0],
            "Picture IMG002 does not belong to group IMG001",
            test,
        )

    def test_picture_group_add_pictures_wrong_trip(self):
        test = "Add picture: wrong trip"
        picture_group = self.repository.trips["Malta"]["IMG001"]
        picture = [
            p
            for p in self.repository.trips["Georgia"]["IMG010"].pictures[""]
            if p.path.endswith(os.path.join("Georgia", "IMG010.CR2"))
        ]
        picture = picture[0]
        with self.assertRaises(ValueError) as cm:
            picture_group.add_picture(picture)
        self.assertEqual(type(cm.exception), ValueError, test)
        self.assertEqual(
            cm.exception.args[0],
            "Picture IMG010 has the wrong trip for group IMG001",
            test,
        )

    def test_picture_group_add_pictures_ok(self):
        test = "Add picture: OK in existing group"
        new_image_path = os.path.join(
            BASE_FOLDER, "Temporary", "Malta", "IMG002_DT.jpg"
        )
        self.all_files.append(new_image_path)
        open(new_image_path, "w").close()

        picture_group = self.repository.trips["Malta"]["IMG002"]
        location = [loc for loc in self.locations if loc.name == "Temporary"][0]
        self.repository.add_picture(picture_group, location, new_image_path)

        self.assertIn("DT", picture_group.pictures, test)
        new_picture = picture_group.pictures["DT"][0]
        self.assertEqual(new_picture.path, new_image_path, test)

    def test_picture_group_remove_picture_validations(self):
        # Negative deletion test
        test = "Remove picture : wrong trip for group"
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = self.repository.trips["Georgia"]["IMG010"].pictures[""][0]
        with self.assertRaises(ValueError) as cm:
            picture_group.remove_picture(picture)
            self.assertEqual(type(cm.exception), ValueError, test)
            self.assertEqual(
                cm.exception.args[0],
                "Picture IMG010 has the wrong trip for group IMG002",
                test,
            )

    def test_picture_group_deletion(self):
        # Remove image without deleting the actual files
        # This is because coverage doesn't realize it has been tested indirectly
        picture_group = self.repository.trips["Korea"]["IMG030"]
        nb_groups_before_deletion = len(self.repository.picture_groups)
        pictures = []
        for conversion_type in picture_group.pictures:
            for picture in picture_group.pictures[conversion_type]:
                pictures.append(picture)
        for picture in pictures:
            picture_group.remove_picture(picture)
        self.assertEqual(
            len(self.repository.picture_groups),
            nb_groups_before_deletion - 1,
            "picture_group deletion when pictures are removed",
        )

    def test_picture_group_name_change(self):
        # Adding a picture that is more "basic" than an existing group
        # Situation: group 'IMG011_convert' exists, now we find picture IMG011.CR2
        # The group's name should be changed to IMG011
        # The conversion types should change as well
        picture_group = self.repository.trips["Georgia"]["IMG011_convert"]
        new_picture = Picture(
            self.locations, os.path.join(BASE_FOLDER, "DCIM", "IMG011.CR2")
        )
        picture_group.add_picture(new_picture)

        self.assertEqual(
            picture_group.name,
            "IMG011",
            "Group name change: name has changed",
        )
        self.assertEqual(
            picture_group.trip,
            "Georgia",
            "Group name change: trip has not changed",
        )
        self.assertIn(
            "",
            picture_group.pictures,
            "Group name change: empty conversion type exists",
        )
        self.assertIn(
            "convert",
            picture_group.pictures,
            "Group name change: '_convert' conversion type exists",
        )
