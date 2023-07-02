import os
import unittest
import datetime
import logging

import pydive.models.database as databasemodel

from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType
from pydive.models.repository import Repository
from pydive.models.picture import Picture, StorageLocationCollision

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"


class TestRepository(unittest.TestCase):
    def setUp(self):
        try:
            os.remove(BASE_FOLDER)
        except OSError:
            pass
        self.all_folders = [
            BASE_FOLDER,
            BASE_FOLDER + "DCIM/",
            BASE_FOLDER + "DCIM/Sweden/",
            BASE_FOLDER + "Temporary/",
            BASE_FOLDER + "Temporary/Malta/",
            BASE_FOLDER + "Temporary/Georgia/",
            BASE_FOLDER + "Temporary/Korea/",
            BASE_FOLDER + "Temporary/Sweden/",
            BASE_FOLDER + "Archive/",
            BASE_FOLDER + "Archive/Malta/",
            BASE_FOLDER + "Archive/Korea/",
            BASE_FOLDER + "Archive/Sweden/",
            BASE_FOLDER + "Archive_outside_DB/",
            BASE_FOLDER + "Archive_outside_DB/Egypt/",
            BASE_FOLDER + "Empty/",
        ]
        for folder in self.all_folders:
            os.makedirs(folder, exist_ok=True)
        self.all_files = [
            BASE_FOLDER + "DCIM/IMG001.CR2",
            BASE_FOLDER + "DCIM/IMG002.CR2",
            BASE_FOLDER + "DCIM/IMG010.CR2",
            BASE_FOLDER + "DCIM/IMG020.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG001.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG001_RT.jpg",
            BASE_FOLDER + "Temporary/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG002_RT.jpg",
            BASE_FOLDER + "Archive/Malta/IMG001.CR2",
            BASE_FOLDER + "Archive/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010_RT.jpg",
            BASE_FOLDER + "Temporary/Georgia/IMG011_convert.jpg",
            BASE_FOLDER + "Temporary/Korea/IMG030.CR2",
            BASE_FOLDER + "Archive/Korea/IMG030_RT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG040.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG041.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "Archive/Sweden/IMG040_convert.jpg",
            BASE_FOLDER + "Archive_outside_DB/Egypt/IMG037.CR2",
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
                    id=1, name="Camera", type="folder", path=BASE_FOLDER + "DCIM/"
                ),
                # Test without final "/" in path
                StorageLocation(
                    id=2,
                    name="Temporary",
                    type="folder",
                    path=BASE_FOLDER + "Temporary",
                ),
                StorageLocation(
                    id=3,
                    name="Archive",
                    type=StorageLocationType["folder"],
                    path=BASE_FOLDER + "Archive/",
                ),
                StorageLocation(
                    id=4,
                    name="Inexistant",
                    type="folder",
                    path=BASE_FOLDER + "Inexistant/",
                ),
                StorageLocation(
                    id=5,
                    name="No picture here",
                    type="folder",
                    path=BASE_FOLDER + "Empty/",
                ),
                StorageLocation(
                    id=6,
                    name="Dive log",
                    type="file",
                    path=BASE_FOLDER + "Archives/test.txt",
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
            if p.path.endswith("Temporary/Malta/IMG001.CR2")
        ]
        picture = picture[0]

        test = "String representation: picture"
        self.assertEqual(
            str(picture),
            "('IMG001', 'Malta', 'Temporary', '"
            + BASE_FOLDER
            + "Temporary/Malta/IMG001.CR2')",
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
                path=BASE_FOLDER + "Temporary/Malta",
            )
            self.repository.load_pictures([new_location])

    def test_storage_location_add(self):
        test = "Add a storage location: Count trips"
        nb_trips_before = len(self.repository.trips)
        new_location = StorageLocation(
            id=999,
            name="Outside_DB",
            type="folder",
            path=BASE_FOLDER + "Archive_outside_DB/",
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
            path=BASE_FOLDER + "Temporary/Malta",
        )
        with self.assertRaises(ValueError, msg=test) as cm:
            self.repository.load_pictures([new_location])
            self.assertEqual(type(cm.exception), StorageLocationCollision, test)

    def helper_check_paths(self, should_exist, test):
        # TODO: Test with actual signals & remove this ugly workaround
        import time

        time.sleep(2 + 2 * len(should_exist))
        all_files_checked = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG041.CR2",
            BASE_FOLDER + "Archive/Sweden/IMG040.CR2",
            BASE_FOLDER + "Archive/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "Archive/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "Archive/Sweden/IMG040_convert.CR2",
            BASE_FOLDER + "Archive/Sweden/IMG041.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG040.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG040_convert.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG041.CR2",
        ]

        initial_files = [
            BASE_FOLDER + "Temporary/Sweden/IMG040.CR2",
            BASE_FOLDER + "Temporary/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "Temporary/Sweden/IMG041.CR2",
            BASE_FOLDER + "Archive/Sweden/IMG040_convert.jpg",
        ]

        self.all_files += should_exist
        for path in all_files_checked:
            if path in should_exist or path in initial_files:
                self.assertTrue(os.path.exists(path), f"{test} - File {path}")
            else:
                self.assertFalse(os.path.exists(path), f"{test} - File {path}")
        self.all_files = list(set(self.all_files))

        # #file_list = "\n".join(sorted(self.all_files))
        # #print('self.files')
        # #print(file_list)

        # #file_list = "\n".join(sorted(initial_files))
        # #print('initial_files')
        # #print(file_list)

        # #print('system')
        # #os.system(f'find {BASE_FOLDER} -type f')

    # List of Repository.copy_pictures tests
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
    def test_repository_copy_pictures_all_parameters(self):
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

        new_files = [
            BASE_FOLDER + "Archive/Sweden/IMG040.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_missing_conversion_method(self):
        test = "Picture copy: all parameters provided except conversion_method"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = self.repository.trips[trip]["IMG040"]
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.jpg",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_missing_picture_group(self):
        test = "Picture copy: all parameters provided except picture_group (copies some of the trip)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = ""

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG041.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_missing_source_location(self):
        test = "Picture copy: all parameters provided except source_location (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
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

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_missing_trip(self):
        # This test gives the same result as "all parameters" since trip will be ignored
        test = "Picture copy: all parameters provided except trip (copies 1 picture)"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_conversion_method_and_picture_group(self):
        test = "Picture copy: conversion_method and picture_group provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

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

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths([], test)

    def test_repository_copy_pictures_conversion_method_and_trip(self):
        test = "Picture copy: conversion_method and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG041.CR2",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_picture_group_and_source_location(self):
        test = "Picture copy: picture_group and source_location provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_picture_group_and_trip(self):
        test = "Picture copy: picture_group and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.jpg",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_copy_pictures_source_location_and_trip(self):
        test = "Picture copy: source_location and trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = self.database.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG041.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.jpg",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

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

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths([], test)

    def test_repository_copy_pictures_picture_group(self):
        test = "Picture copy: only picture_group provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = self.repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",  # Existing
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",  # Existing
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",  # Existing
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.jpg",  # Existing
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

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

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths([], test)

    def test_repository_copy_pictures_trip(self):
        test = "Picture copy: only trip provided"
        target_location = self.database.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        process = self.repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            BASE_FOLDER + "DCIM/Sweden/IMG040.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_RT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG040_DT.jpg",
            BASE_FOLDER + "DCIM/Sweden/IMG041.CR2",
            BASE_FOLDER + "DCIM/Sweden/IMG040_convert.jpg",
        ]
        process.finished.connect(lambda: self.helper_check_paths(new_files, test))

        # TODO: Test with actual signals & remove this ugly workaround
        self.helper_check_paths(new_files, test)

    def test_repository_generate_pictures(self):
        # Generate / convert pictures
        # TODO: test > write this function
        pass
        # Need test cases for each situation:
        # source_location=None or provided, trip=None or provided, picture_group=None or provided, different conversion_methods

    def test_repository_change_trip_pictures(self):
        # Change trip (with actual changes)
        # TODO: test > write this function
        pass

        # Need test cases for each situation:
        # source_trip=None or provided, picture_group=None or provided

    def test_repository_change_trip_pictures_finished(self):
        # Change trip (without actual changes - meant to increase coverage
        # TODO: test > write this function
        pass

        # Need test cases for each situation:
        # source_trip=None or provided, picture_group=None or provided

    def test_repository_remove_pictures_1_picture(self):
        # TODO: Apply the workaround from creating files
        test = "Picture remove: actual deletion of 1 picture"
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        path = picture.path
        process = self.repository.remove_pictures(test, None, picture_group, picture)
        process.finished.connect(lambda: self.assertFalse(os.path.exists(path), test))

        self.assertEqual(str(process), test + " (1 tasks)", test)

        # TODO: Test with actual signals & remove this ugly workaround
        import time

        time.sleep(2)
        self.assertFalse(os.path.exists(path), test)

    def test_repository_remove_pictures_trip(self):
        test = "Picture remove: actual deletion of a trip"
        picture_files = [p for p in self.all_files if "/Korea/" in p]

        process = self.repository.remove_pictures(test, trip="Korea")
        process.finished.connect(
            lambda: all(
                self.assertFalse(
                    os.path.exists(path),
                    test,
                )
                for path in picture_files
            )
        )

        # TODO: Test with actual signals & remove this ugly workaround
        import time

        time.sleep(2)
        all(
            self.assertFalse(
                os.path.exists(path),
                test,
            )
            for path in picture_files
        )

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
        # This is because coverage doesn't realize it has been tested indirectly
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
        # This is because coverage doesn't realize it has been tested indirectly
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
            if p.path.endswith("Georgia/IMG010.CR2")
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
        new_image_path = BASE_FOLDER + "Temporary/Malta/IMG002_DT.jpg"
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
        new_picture = Picture(self.locations, BASE_FOLDER + "DCIM/IMG011.CR2")
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
