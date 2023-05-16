import os
import unittest
import datetime

import pydive.models.database as databasemodel

from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType
from pydive.models.repository import Repository
from pydive.models.picture import Picture, StorageLocationCollision

DATABASE_FILE = "test.sqlite"
database = databasemodel.Database(DATABASE_FILE)

try:
    os.remove(DATABASE_FILE)
except OSError:
    pass

BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.all_folders = [
            BASE_FOLDER,
            BASE_FOLDER + "DCIM/",
            BASE_FOLDER + "Temporary/",
            BASE_FOLDER + "Temporary/Malta/",
            BASE_FOLDER + "Temporary/Georgia/",
            BASE_FOLDER + "Archive/",
            BASE_FOLDER + "Archive/Malta/",
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
            BASE_FOLDER + "Temporary/Malta/IMG002.CR2",
            BASE_FOLDER + "Archive/Malta/IMG001.CR2",
            BASE_FOLDER + "Archive/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010_RT.jpg",
            BASE_FOLDER + "Temporary/Georgia/IMG011_convert.jpg",
            BASE_FOLDER + "Archive_outside_DB/Egypt/IMG037.CR2",
        ]
        for test_file in self.all_files:
            open(test_file, "w").close()

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

    def tearDown(self):
        # Delete database
        self.database.session.close()
        self.database.engine.dispose()
        os.remove(DATABASE_FILE)

        # Delete folders
        for test_file in self.all_files:
            os.remove(test_file)
        for folder in sorted(self.all_folders, reverse=True):
            os.rmdir(folder)

    def test_readonly(self):
        # Load the pictures
        storage_locations = self.database.storagelocations_get_folders()
        locations = {loc.name: loc.path for loc in storage_locations}
        repository = Repository(locations)

        # Check the recognition worked
        self.assertEqual(
            len(repository.trips),
            3,
            "There are 3 trips",
        )
        self.assertEqual(
            len(repository.trips[""]),
            1,
            "There is 1 picture group with no trip",
        )
        self.assertEqual(
            len(repository.trips["Malta"]),
            2,
            "There are 2 picture groups in the Malta trip",
        )

        # String representations
        picture_group = repository.trips["Malta"]["IMG001"]
        self.assertEqual(
            str(picture_group),
            "('IMG001', 'Malta', '1 pictures')",
        )

        picture = [
            p
            for p in repository.pictures
            if p.path.endswith("Temporary/Malta/IMG001.CR2")
        ]
        picture = picture[0]
        self.assertEqual(
            str(picture),
            "('IMG001', 'Malta', 'Temporary', '"
            + BASE_FOLDER
            + "Temporary/Malta/IMG001.CR2')",
            "String representation of a picture: name, trip, folder name, path",
        )

        with self.assertRaises(StorageLocationCollision):
            repository.load_pictures({"Used path": BASE_FOLDER + "Temporary/Malta"})

    def test_modifications(self):
        # Load the pictures
        storage_locations = self.database.storagelocations_get_folders()
        locations = {loc.name: loc.path for loc in storage_locations}
        repository = Repository(locations)

        # Add a new storage location
        repository.load_pictures({"Outside_DB": BASE_FOLDER + "Archive_outside_DB/"})
        self.assertEqual(
            len(repository.trips),
            4,
            "There are now 4 trips",
        )

        test_name = "Try to use subfolder of existing folder"
        test_repo = Repository(locations)
        with self.assertRaises(ValueError) as cm:
            test_repo.load_pictures({"Used path": BASE_FOLDER + "Temporary/Malta"})
            self.assertEqual(type(cm.exception), StorageLocationCollision, test_name)

        test_name = "Load images in wrong group (based on file name)"
        picture_group = repository.trips["Malta"]["IMG001"]
        picture = [p for p in repository.pictures if p.path.endswith("IMG002.CR2")]
        picture = picture[0]
        with self.assertRaises(ValueError) as cm:
            picture_group.add_picture(picture)
        self.assertEqual(type(cm.exception), ValueError, test_name)
        self.assertEqual(
            cm.exception.args[0],
            "Picture IMG002 does not belong to group IMG001",
            test_name,
        )

        test_name = "Load images in wrong group (based on trip)"
        picture_group = repository.trips["Malta"]["IMG001"]
        picture = [
            p for p in repository.pictures if p.path.endswith("Georgia/IMG010.CR2")
        ]
        picture = picture[0]
        with self.assertRaises(ValueError) as cm:
            picture_group.add_picture(picture)
        self.assertEqual(type(cm.exception), ValueError, test_name)
        self.assertEqual(
            cm.exception.args[0],
            "Picture IMG010 has the wrong trip for group IMG001",
            test_name,
        )

    def test_group_name_change(self):
        # Load the pictures
        storage_locations = self.database.storagelocations_get_folders()
        locations = {loc.name: loc.path for loc in storage_locations}
        repository = Repository(locations)

        # Adding a picture that is more "basic" than an existing group
        # Situation: group 'IMG011_convert' exists, now we find picture IMG011.CR2
        # The group's name should be changed to IMG011
        # The conversion types should change as well
        picture_group = repository.trips["Georgia"]["IMG011_convert"]
        new_picture = Picture(locations, BASE_FOLDER + "DCIM/IMG011.CR2")
        picture_group.add_picture(new_picture)

        self.assertEqual(
            picture_group.name,
            "IMG011",
            "The group name is IMG011",
        )
        self.assertEqual(
            picture_group.trip,
            "Georgia",
            "The group trip is Georgia",
        )
        self.assertIn(
            "",
            picture_group.pictures,
            "The group has pictures with empty conversion type",
        )
        self.assertIn(
            "_convert",
            picture_group.pictures,
            "The group has pictures with conversion type _convert",
        )