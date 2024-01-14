import os
import sys
import pytest
from PyQt5 import QtCore, QtTest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

from models.storagelocation import StorageLocation
from models.picture import Picture, StorageLocationCollision
from models.category import Category


class TestRepository:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, qtbot, pydive_fake_pictures):
        self.all_files = pydive_fake_pictures

    def helper_check_paths(self, test, should_exist=[], should_not_exist=[]):
        QtCore.QThreadPool.globalInstance().waitForDone()
        # Add "should exist" to "all_files" so they get deleted later
        self.all_files += should_exist
        self.all_files = list(set(self.all_files))

        # We check all files: both existing and non-existing
        all_files_checked = set(self.all_files + should_not_exist)
        should_exist = [
            f
            for f in self.all_files
            if f not in should_not_exist
            and os.path.join(pytest.BASE_FOLDER, f) not in should_not_exist
        ]
        for path in all_files_checked:
            absolute_path = path
            if pytest.BASE_FOLDER not in path:
                absolute_path = os.path.join(pytest.BASE_FOLDER, path)
            if path in should_exist:
                assert os.path.exists(absolute_path), f"{test} - File {absolute_path}"
            else:
                assert not os.path.exists(
                    absolute_path
                ), f"{test} - File {absolute_path}"

    def test_load_pictures_trip_recognition(self, pydive_repository):
        # Check if recognition worked
        test = "Load pictures: Count trips"
        assert len(pydive_repository.trips) == 8, test

        test = "Load pictures: Count pictures with no trips"
        assert len(pydive_repository.trips[""]) == 4, test

        test = "Load pictures: Count pictures in a given trip"
        assert len(pydive_repository.trips["Malta"]) == 2, test

        test = "Load pictures: Check picture's trip"
        picture_group = pydive_repository.trips["Malta"]["IMG001"]
        picture = picture_group.categories["Temporary"][""][0]
        assert picture.trip == "Malta", test
        assert picture.category == "", test

        test = "Load pictures: Check picture's category"
        picture = picture_group.categories["Temporary"]["Top"][0]
        assert picture.trip == "Malta", test
        assert picture.category.name == "Top", test

        test = "Load pictures: Check unknown category"
        picture_group = pydive_repository.trips["Malta/Unknown_category"]["IMG001_RT"]
        picture = picture_group.categories["Temporary"][""][0]
        assert picture.trip == "Malta/Unknown_category", test

    def test_string_representation(self, pydive_repository):
        test = "String representation: picture group"
        picture_group = pydive_repository.trips["Malta"]["IMG001"]
        assert str(picture_group) == "('IMG001', 'Malta', '5 pictures')", test

        picture = [
            p
            for p in picture_group.pictures[""]
            if p.path.endswith(
                os.path.join("Temporary", "Malta", "Sélection", "IMG001.CR2")
            )
        ]
        picture = picture[0]

        test = "String representation: picture"
        assert (
            str(picture)
            == "IMG001 in Temporary during Malta - path "
            + os.path.join(
                pytest.BASE_FOLDER, "Temporary", "Malta", "Sélection", "IMG001.CR2"
            )
            + ""
        ), test

        test = "String representation: picture.filename"
        assert picture.filename == "IMG001.CR2", test

    def test_load_pictures_storage_location_collision(
        self, pydive_repository, pydive_db
    ):
        test = "Load pictures: storage location collision"
        with pytest.raises(StorageLocationCollision):
            new_location = StorageLocation(
                id=999,
                name="Used path",
                type="picture_folder",
                path=os.path.join(pytest.BASE_FOLDER, "Temporary", "Malta"),
            )
            pydive_db.session.add(new_location)
            pydive_db.session.commit()
            pydive_repository.load_pictures()
            pytest.fail(test)

    def test_storage_location_add(self, pydive_repository, pydive_db):
        test = "Add a storage location: Count trips"
        nb_trips_before = len(pydive_repository.trips)
        new_location = StorageLocation(
            id=999,
            name="Outside_DB",
            type="picture_folder",
            path=os.path.join(pytest.BASE_FOLDER, "Archive_outside_DB"),
        )
        pydive_db.session.add(new_location)
        pydive_db.session.commit()
        pydive_repository.load_pictures()
        assert len(pydive_repository.trips) == nb_trips_before + 1, test

    def test_storage_location_add_with_collision(self, pydive_repository, pydive_db):
        test = "Add a storage location: subfolder of existing folder"
        new_location = StorageLocation(
            id=999,
            name="Used path",
            type="picture_folder",
            path=os.path.join(pytest.BASE_FOLDER, "Temporary", "Malta"),
        )
        pydive_db.session.add(new_location)
        pydive_db.session.commit()
        with pytest.raises(StorageLocationCollision) as cm:
            pydive_repository.load_pictures()
            pytest.fail(test)
        assert cm.value.args[0] == "recognition failed", test

    def test_recognition_with_category_collision(self, pydive_repository, pydive_db):
        test = "Add a category: subfolder of existing folder"
        new_category = Category(
            id=999,
            name="Vrac",
            relative_path="lection",
        )
        pydive_db.session.add(new_category)
        pydive_db.session.commit()
        with pytest.raises(StorageLocationCollision) as cm:
            pydive_repository.load_pictures()
            pytest.fail(test)
        assert cm.value.args[0] == "recognition failed", test

    # List of Repository.copy_pictures tests - "KO" denotes when a ValueError is raised
    # The copy with category is tested only in test_repository_copy_pictures_all_parameters
    # Since that parameter intervenes only at the end, it's not really useful to test all cases
    # source_location   trip    picture_group   conversion_method
    #       X             X             X               X       test_repository_copy_pictures_all_parameters
    #       X             X             X               X       test_repository_copy_pictures_missing_category

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

    #                                                           test_repository_copy_pictures_no_parameter

    def test_repository_process_group_finished_signal(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided (copies 1 picture)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = pydive_db.conversionmethods_get_by_suffix("RT")

        process = pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )
        QtCore.QThreadPool.globalInstance().waitForDone()

        expected_signal = QtTest.QSignalSpy(process.finished)
        assert expected_signal.isValid()

        new_files = [
            os.path.join("Archive", "Sweden", "IMG040_RT.jpg"),
        ]
        self.all_files += new_files

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_all_parameters(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided (copies 1 picture)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = ""
        target_category = pydive_db.category_get_by_name("Top")

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
            target_category,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "Sélection", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_category(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided (copies 1 picture)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = ""

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_conversion_method(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided except conversion_method"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_conversion_method_with_category(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided except conversion_method"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = None
        target_category = pydive_db.category_get_by_name("Top")

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
            target_category,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "Sélection", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "Sélection", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "Sélection", "IMG040_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_picture_group(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided except picture_group (copies some of the trip)"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = ""

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_source_location(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: all parameters provided except source_location (copies 1 picture)"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = ""

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_missing_trip(self, pydive_repository, pydive_db):
        # This test gives the same result as "all parameters" since trip will be ignored
        test = "Picture copy: all parameters provided except trip (copies 1 picture)"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method_and_picture_group(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: conversion_method and picture_group provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]
        conversion_method = ""

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method_and_source_location(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: conversion_method and source_location provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None
        conversion_method = ""

        with pytest.raises(ValueError) as cm:
            pydive_repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repository_copy_pictures_conversion_method_and_trip(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: conversion_method and trip provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_picture_group_and_source_location(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: picture_group and source_location provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_picture_group_and_trip(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: picture_group and trip provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_source_location_and_trip(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: source_location and trip provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG041.CR2"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_conversion_method(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: only conversion_method provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = None
        conversion_method = ""

        with pytest.raises(ValueError) as cm:
            pydive_repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repository_copy_pictures_picture_group(self, pydive_repository, pydive_db):
        test = "Picture copy: only picture_group provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_source_location(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: only source_location provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None
        conversion_method = None

        with pytest.raises(ValueError) as cm:
            pydive_repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repository_copy_pictures_trip(self, pydive_repository, pydive_db):
        test = "Picture copy: only trip provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = "Sweden"
        picture_group = None
        conversion_method = None

        pydive_repository.copy_pictures(
            test,
            target_location,
            source_location,
            trip,
            picture_group,
            conversion_method,
        )

        new_files = [
            os.path.join("DCIM", "Sweden", "IMG040.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_RT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG040_DT.jpg"),
            os.path.join("DCIM", "Sweden", "IMG041.CR2"),
            os.path.join("DCIM", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repository_copy_pictures_no_parameter(self, pydive_repository, pydive_db):
        test = "Picture copy: no parameter provided"
        target_location = pydive_db.storagelocation_get_by_name("Camera")
        source_location = None
        trip = None
        picture_group = None
        conversion_method = None

        with pytest.raises(ValueError) as cm:
            pydive_repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repository_copy_pictures_picture_inexistant(
        self, pydive_repository, pydive_db
    ):
        test = "Picture copy: inexistant picture for given parameters"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]
        conversion_method = "ZZZ"

        with pytest.raises(FileNotFoundError) as cm:
            pydive_repository.copy_pictures(
                test,
                target_location,
                source_location,
                trip,
                picture_group,
                conversion_method,
            )
        assert cm.value.args[0] == "No source image found", test

        self.helper_check_paths(test)

    # List of Repository.change_trip_pictures tests - "KO" denotes when a ValueError is raised
    #  picture_group   source_trip
    #       X                X        test_repository_change_trip_all_parameters

    #       X                         test_repository_change_trip_picture_group
    #                        X        test_repository_change_trip_source_trip

    #                                 test_repository_change_trip_no_parameter

    def test_repository_change_trip_all_parameters(self, pydive_repository):
        test = "Picture change trip: all parameters provided"
        target_trip = "Korea"
        source_trip = "Sweden"
        picture_group = pydive_repository.trips[source_trip]["IMG040"]

        pydive_repository.change_trip_pictures(
            test,
            target_trip,
            source_trip,
            picture_group,
        )

        new_files = [
            os.path.join("Temporary", "Korea", "IMG040.CR2"),
            os.path.join("Temporary", "Korea", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Korea", "IMG040_DT.jpg"),
            os.path.join("Archive", "Korea", "IMG040_convert.jpg"),
        ]

        should_not_exist = [
            os.path.join("Temporary", "Sweden", "IMG040.CR2"),
            os.path.join("Temporary", "Sweden", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Sweden", "IMG040_DT.jpg"),
            os.path.join("Archive", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_change_trip_picture_group(self, pydive_repository, qtbot):
        test = "Picture change trip: only picture group provided"
        target_trip = "Korea"
        source_trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG040"]

        with qtbot.waitSignal(picture_group.pictureRemoved):
            pydive_repository.change_trip_pictures(
                test,
                target_trip,
                source_trip,
                picture_group,
            )
        # Make sure models have time to update
        qtbot.waitUntil(lambda: "IMG040" not in pydive_repository.trips["Sweden"])

        new_files = [
            os.path.join("Temporary", "Korea", "IMG040.CR2"),
            os.path.join("Temporary", "Korea", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Korea", "IMG040_DT.jpg"),
            os.path.join("Archive", "Korea", "IMG040_convert.jpg"),
        ]

        should_not_exist = [
            os.path.join("Temporary", "Sweden", "IMG040.CR2"),
            os.path.join("Temporary", "Sweden", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Sweden", "IMG040_DT.jpg"),
            os.path.join("Archive", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

        # Check pictures are updates (only IMG040.CR2 is actually checked)
        picture = pydive_repository.trips["Korea"]["IMG040"].pictures[""][0]
        new_path = os.path.join("Temporary", "Korea", "IMG040.CR2")
        assert "IMG040" not in pydive_repository.trips["Sweden"], test
        assert "IMG040" in pydive_repository.trips["Korea"], test
        assert picture.path == os.path.join(pytest.BASE_FOLDER, new_path), test
        assert picture.trip == target_trip, test

    def test_repository_change_trip_source_trip(self, pydive_repository):
        test = "Picture change trip: only trip provided"
        target_trip = "Korea"
        source_trip = "Sweden"
        picture_group = None

        pydive_repository.change_trip_pictures(
            test,
            target_trip,
            source_trip,
            picture_group,
        )

        new_files = [
            os.path.join("Temporary", "Korea", "IMG040.CR2"),
            os.path.join("Temporary", "Korea", "IMG041.CR2"),
            os.path.join("Temporary", "Korea", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Korea", "IMG040_DT.jpg"),
            os.path.join("Archive", "Korea", "IMG040_convert.jpg"),
        ]

        should_not_exist = [
            os.path.join("Temporary", "Sweden", "IMG040.CR2"),
            os.path.join("Temporary", "Sweden", "IMG041.CR2"),
            os.path.join("Temporary", "Sweden", "IMG040_RT.jpg"),
            os.path.join("Temporary", "Sweden", "IMG040_DT.jpg"),
            os.path.join("Archive", "Sweden", "IMG040_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_change_trip_no_parameter(self, pydive_repository):
        test = "Picture change trip: no parameter provided"
        target_trip = "Korea"
        source_trip = None
        picture_group = None

        with pytest.raises(ValueError) as cm:
            pydive_repository.change_trip_pictures(
                test,
                target_trip,
                source_trip,
                picture_group,
            )
        assert (
            cm.value.args[0] == "Either source_trip or picture_group must be provided"
        ), test

        self.helper_check_paths(test)

    def test_repository_change_trip_target_exists(self, pydive_repository):
        test = "Picture change trip: target group exists"
        target_trip = "Island"
        source_trip = "Romania"
        picture_group = pydive_repository.trips[source_trip]["IMG050"]

        pydive_repository.change_trip_pictures(
            test,
            target_trip,
            source_trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Island", "IMG050.CR2"),
            os.path.join("Archive", "Island", "IMG050_convert.jpg"),
        ]

        should_not_exist = [
            # This will still exist since the target file exists
            os.path.join("Archive", "Romania", "IMG050_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repository_remove_pictures_1_picture(self, pydive_repository):
        test = "Picture remove: actual deletion of 1 picture"
        picture_group = pydive_repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        path = picture.path

        process = pydive_repository.remove_pictures(test, None, picture_group, picture)

        assert str(process) == test + " (1 tasks)", test
        self.helper_check_paths(test, [], [path])

    def test_repository_remove_pictures_trip(self, pydive_repository):
        test = "Picture remove: actual deletion of a trip"
        picture_files = [
            p for p in self.all_files if os.path.sep + "Korea" + os.path.sep in p
        ]

        pydive_repository.remove_pictures(test, trip="Korea")

        self.helper_check_paths(test, [], picture_files)

    def test_repository_remove_pictures_validations(self, pydive_repository):
        # Delete image without changing structure of .pictures and .locations
        test = "Remove picture: At least 1 trip/picture reference is required"
        with pytest.raises(ValueError) as cm:
            pydive_repository.remove_pictures(test)
        assert (
            cm.value.args[0] == "Either trip, picture_group or picture must be provided"
        ), test

        test = "Remove picture: picture_group required if picture provided"
        picture_group = pydive_repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        with pytest.raises(ValueError) as cm:
            pydive_repository.remove_pictures(test, picture=picture)
        assert (
            cm.value.args[0] == "picture_group is required if picture is provided"
        ), test

    def test_repository_remove_picture_no_structure_change(self, pydive_repository):
        # Remove image without deleting the actual files
        # This allows detection by coverage
        test = "Remove picture, keep .pictures and.locations"
        picture_group = pydive_repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        location_initial_count = len(picture_group.locations["Temporary"])
        conversion_type_initial_count = len(picture_group.pictures[""])
        path = picture.path
        pydive_repository.remove_picture(picture_group, picture.location, picture.path)
        assert os.path.exists(path), test + ": file not deleted (on purpose)"
        assert (
            len(picture_group.locations["Temporary"]) == location_initial_count - 1
        ), (test + ": deletion from picture_group.locations")
        assert len(picture_group.pictures[""]) == conversion_type_initial_count - 1, (
            test + ": deletion from picture_group.pictures"
        )

    def test_repository_remove_picture_structure_change(self, pydive_repository):
        # Remove image without deleting the actual files
        # This allows detection by coverage
        test = "Remove picture, remove keys from .pictures and.locations"
        picture_group = pydive_repository.trips["Korea"]["IMG030"]
        picture = picture_group.pictures["RT"][0]
        path = picture.path
        pydive_repository.remove_picture(picture_group, picture.location, picture.path)
        assert os.path.exists(path), test + ": file not deleted (on purpose)"
        assert "RT" not in picture_group.pictures, (
            test + ": .pictures no longer has RT as key"
        )
        assert "Archive" not in picture_group.locations, (
            test + ": .locations no longer has Archive as key"
        )

    def test_picture_group_add_pictures_wrong_name(self, pydive_repository):
        test = "Add picture: wrong group name"
        picture_group = pydive_repository.trips["Malta"]["IMG001"]
        picture = [
            p
            for p in pydive_repository.trips["Malta"]["IMG002"].pictures[""]
            if p.path.endswith("IMG002.CR2")
        ]

        picture = picture[0]
        with pytest.raises(ValueError) as cm:
            picture_group.add_picture(picture)
        assert (
            cm.value.args[0] == "Picture IMG002 does not belong to group IMG001"
        ), test

    def test_picture_group_add_pictures_wrong_trip(self, pydive_repository):
        test = "Add picture: wrong trip"
        picture_group = pydive_repository.trips["Malta"]["IMG001"]
        picture = [
            p
            for p in pydive_repository.trips["Georgia"]["IMG010"].pictures[""]
            if p.path.endswith(os.path.join("Georgia", "IMG010.CR2"))
        ]
        picture = picture[0]
        with pytest.raises(ValueError) as cm:
            picture_group.add_picture(picture)
        assert (
            cm.value.args[0] == "Picture IMG010 has the wrong trip for group IMG001"
        ), test

    def test_picture_group_add_pictures_ok(self, pydive_db, pydive_repository):
        test = "Add picture: OK in existing group"
        new_image_path = os.path.join(
            pytest.BASE_FOLDER, "Temporary", "Malta", "IMG002_DT.jpg"
        )
        self.all_files.append(new_image_path)
        open(new_image_path, "w").close()

        picture_group = pydive_repository.trips["Malta"]["IMG002"]
        locations = pydive_db.storagelocations_get_picture_folders()
        location = [loc for loc in locations if loc.name == "Temporary"][0]
        pydive_repository.add_picture(picture_group, location, new_image_path)

        assert "DT" in picture_group.pictures, test
        new_picture = picture_group.pictures["DT"][0]
        assert new_picture.path == new_image_path, test

    def test_picture_group_remove_picture_validations(self, pydive_repository):
        # Negative deletion test
        test = "Remove picture : wrong trip for group"
        picture_group = pydive_repository.trips["Malta"]["IMG002"]
        picture = pydive_repository.trips["Georgia"]["IMG010"].pictures[""][0]
        with pytest.raises(ValueError) as cm:
            picture_group.remove_picture(picture)
        assert (
            cm.value.args[0] == "Picture IMG010 has the wrong trip for group IMG002"
        ), test

    def test_picture_group_deletion(self, pydive_repository):
        # Remove image without deleting the actual files
        # This is because coverage doesn't realize it has been tested indirectly
        picture_group = pydive_repository.trips["Korea"]["IMG030"]
        nb_groups_before_deletion = len(pydive_repository.picture_groups)
        pictures = []
        for conversion_type in picture_group.pictures:
            for picture in picture_group.pictures[conversion_type]:
                pictures.append(picture)
        for picture in pictures:
            picture_group.remove_picture(picture)
        assert (
            len(pydive_repository.picture_groups) == nb_groups_before_deletion - 1
        ), "picture_group deletion when pictures are removed"

    def test_picture_group_name_change(self, pydive_repository, pydive_db):
        # Adding a picture that is more "basic" than an existing group
        # Situation: group 'IMG011_convert' exists, now we find picture IMG011.CR2
        # The group's name should be changed to IMG011
        # The conversion types should change as well
        picture_group = pydive_repository.trips["Georgia"]["IMG011_convert"]
        locations = pydive_db.storagelocations_get_picture_folders()
        categories = pydive_db.categories_get()
        new_picture = Picture(
            locations,
            categories,
            os.path.join(pytest.BASE_FOLDER, "DCIM", "IMG011.CR2"),
        )
        picture_group.add_picture(new_picture)

        assert picture_group.name == "IMG011", "Group name change: name has changed"
        assert (
            picture_group.trip == "Georgia"
        ), "Group name change: trip has not changed"
        assert (
            "" in picture_group.pictures
        ), "Group name change: empty conversion type exists"
        assert (
            "convert" in picture_group.pictures
        ), "Group name change: '_convert' conversion type exists"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
