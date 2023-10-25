import os
import sys
import pytest
from PyQt5 import QtCore

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database

# This requires actual image files, which are heavy & take time to process
# Hence the separate test class
class TestRepositoryGeneration:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self, pydive_real_pictures):
        self.all_files = pydive_real_pictures
        yield

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

    # List of Repository.generate_pictures tests - "KO" denotes when a ValueError is raised
    #  picture_group   source_location    trip
    #       X                 X             X      test_repo_generate_all_parameters_multiple_methods
    #       X                 X             X      test_repo_generate_all_parameters_single_method

    #       X                 X                    test_repo_generate_missing_trip
    #       X                               X      test_repo_generate_missing_source_location
    #                         X             X      test_repo_generate_missing_picture_group

    #       X                                      test_repo_generate_picture_group
    #                         X                    test_repo_generate_source_location KO
    #                                       X      test_repo_generate_trip

    #                                              test_repo_generate_no_parameter KO

    def test_repo_generate_all_parameters_multiple_methods(
        self, pydive_db, pydive_repository
    ):
        test = "Picture generate: all parameters provided (multiple methods)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get()
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG041"]

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "IMG041_DT.jpg"),
            os.path.join("Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files)

    def test_repo_generate_all_parameters_single_method(
        self, pydive_db, pydive_repository
    ):
        test = "Picture generate: all parameters provided (only DT)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get_by_suffix("DT")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG041"]

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_missing_trip(self, pydive_db, pydive_repository):
        test = "Picture generate: missing trip"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get_by_suffix("DT")
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = pydive_repository.trips["Sweden"]["IMG041"]

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Sweden", "IMG041_RT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_missing_source_location(self, pydive_db, pydive_repository):
        test = "Picture generate: missing source location"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get_by_suffix("DT")
        source_location = None
        trip = "Malta"
        picture_group = pydive_repository.trips["Malta"]["IMG001"]

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Malta", "IMG001_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join("Temporary", "Malta", "IMG001_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_missing_picture_group(self, pydive_db, pydive_repository):
        test = "Picture generate: missing picture group"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = ["DarkTherapee"]
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = None

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Sweden", "IMG040_DT.jpg"),
            os.path.join("Archive", "Sweden", "IMG041_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Sweden", "IMG040_RT.jpg"),
            os.path.join("Archive", "Sweden", "IMG041_RT.jpg"),
            os.path.join("Archive", "Sweden", "IMG041_convert.jpg"),
            os.path.join("Temporary", "Sweden", "IMG041_RT.jpg"),
            os.path.join("Temporary", "Sweden", "IMG041_DT.jpg"),
            os.path.join("Temporary", "Sweden", "IMG041_convert.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_picture_group(self, pydive_db, pydive_repository):
        test = "Picture generate: only picture_group provided"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = ["DT"]
        source_location = None
        trip = None
        picture_group = pydive_repository.trips["Malta"]["IMG001"]

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Malta", "IMG001_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join("Temporary", "Malta", "IMG001_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_source_location(self, pydive_db, pydive_repository):
        test = "Picture generate: only source_location provided"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = "DarkTherapee"
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = None
        picture_group = None

        with pytest.raises(ValueError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repo_generate_trip(self, pydive_db, pydive_repository):
        test = "Picture generate: only trip provided"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = "DT"
        source_location = None
        trip = "Malta"
        picture_group = None

        pydive_repository.generate_pictures(
            test,
            target_location,
            conversion_methods,
            source_location,
            trip,
            picture_group,
        )

        new_files = [
            os.path.join("Archive", "Malta", "IMG001_DT.jpg"),
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]

        should_not_exist = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join("Archive", "Malta", "IMG002_RT.jpg"),
            os.path.join("Temporary", "Malta", "IMG001_DT.jpg"),
            os.path.join("Temporary", "Malta", "IMG002_DT.jpg"),
        ]

        self.helper_check_paths(test, new_files, should_not_exist)

    def test_repo_generate_no_parameter(self, pydive_db, pydive_repository):
        test = "Picture generate: no parameter provided"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get_by_suffix("DT")
        source_location = None
        trip = None
        picture_group = None

        with pytest.raises(ValueError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert cm.value.args[0] == "Either trip or picture_group must be provided", test

        self.helper_check_paths(test)

    def test_repo_generate_no_source_file(self, pydive_db, pydive_repository):
        test = "Picture generate: no source file available in chosen location"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = pydive_db.conversionmethods_get()
        source_location = pydive_db.storagelocation_get_by_name("Archive")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]

        with pytest.raises(FileNotFoundError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert cm.value.args[0] == "No source image found in specified location", test

        self.helper_check_paths(test)

    def test_repo_generate_inexistant_as_str(self, pydive_db, pydive_repository):
        test = "Picture generate: inexistant conversion method (as str)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = "This is a test"
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]

        with pytest.raises(ValueError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert (
            cm.value.args[0]
            == "ConversionMethod This is a test could not be found in database"
        ), test

        self.helper_check_paths(test)

    def test_repo_generate_inexistant_in_array(self, pydive_db, pydive_repository):
        test = "Picture generate: inexistant conversion method (in array)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = ["This is a test"]
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]

        with pytest.raises(ValueError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert (
            cm.value.args[0]
            == "ConversionMethods needs to be an iterable of ConversionMethod"
        ), test

        self.helper_check_paths(test)

    def test_repo_generate_inexistant_as_int(self, pydive_db, pydive_repository):
        test = "Picture generate: inexistant conversion method (as int)"
        target_location = pydive_db.storagelocation_get_by_name("Archive")
        conversion_methods = 123
        source_location = pydive_db.storagelocation_get_by_name("Temporary")
        trip = "Sweden"
        picture_group = pydive_repository.trips[trip]["IMG040"]

        with pytest.raises(ValueError) as cm:
            pydive_repository.generate_pictures(
                test,
                target_location,
                conversion_methods,
                source_location,
                trip,
                picture_group,
            )
        assert (
            cm.value.args[0]
            == "ConversionMethods needs to be an iterable of ConversionMethod"
        ), test

        self.helper_check_paths(test)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
