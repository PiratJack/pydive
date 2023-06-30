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
            if os.path.exists(test_file):
                os.remove(test_file)
        for folder in sorted(self.all_folders, reverse=True):
            os.rmdir(folder)

    def test_readonly(self):
        # Load the pictures
        locations = self.database.storagelocations_get_folders()
        repository = Repository()
        repository.load_pictures(locations)

        # Check the recognition worked
        self.assertEqual(
            len(repository.trips),
            3,
            "There are 3 trips",
        )
        self.assertEqual(
            len(repository.trips[""]),
            4,
            "There are 4 picture groups with no trip",
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
            "('IMG001', 'Malta', '2 pictures')",
        )

        picture = [
            p
            for p in picture_group.pictures[""]
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
        self.assertEqual(
            picture.filename,
            "IMG001.CR2",
            "Picture file name",
        )

        with self.assertRaises(StorageLocationCollision):
            new_location = StorageLocation(
                id=999,
                name="Used path",
                type="folder",
                path=BASE_FOLDER + "Temporary/Malta",
            )
            repository.load_pictures([new_location])

    def test_modifications(self):
        # Load the pictures
        locations = self.database.storagelocations_get_folders()
        repository = Repository()
        repository.load_pictures(locations)

        # Add a new storage location
        new_location = StorageLocation(
            id=999,
            name="Outside_DB",
            type="folder",
            path=BASE_FOLDER + "Archive_outside_DB/",
        )
        repository.load_pictures([new_location])
        self.assertEqual(
            len(repository.trips),
            4,
            "There are now 4 trips",
        )

        test_name = "Try to use subfolder of existing folder"
        test_repo = Repository()
        test_repo.load_pictures(locations)
        with self.assertRaises(ValueError) as cm:
            new_location = StorageLocation(
                id=999,
                name="Used path",
                type="folder",
                path=BASE_FOLDER + "Temporary/Malta",
            )
            test_repo.load_pictures([new_location])
            self.assertEqual(type(cm.exception), StorageLocationCollision, test_name)

        test_name = "Load images in wrong group (based on file name)"
        picture_group = repository.trips["Malta"]["IMG001"]
        picture = [
            p
            for p in repository.trips["Malta"]["IMG002"].pictures[""]
            if p.path.endswith("IMG002.CR2")
        ]

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
            p
            for p in repository.trips["Georgia"]["IMG010"].pictures[""]
            if p.path.endswith("Georgia/IMG010.CR2")
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

        test_name = "Add new image to existing group"
        new_image_path = BASE_FOLDER + "Temporary/Malta/IMG002_DT.jpg"
        self.all_files.append(new_image_path)
        open(new_image_path, "w").close()

        picture_group = repository.trips["Malta"]["IMG002"]
        location = [loc for loc in locations if loc.name == "Temporary"][0]
        repository.add_picture(picture_group, location, new_image_path)

        self.assertIn("DT", picture_group.pictures, test_name)
        new_picture = picture_group.pictures["DT"][0]
        self.assertEqual(new_picture.path, new_image_path, test_name)

        # Delete image without changing structure of .pictures and .locations
        picture_group = repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        location_initial_count = len(picture_group.locations["Temporary"])
        conversion_type_initial_count = len(picture_group.pictures[""])
        path = picture.path
        repository.remove_picture(picture_group, picture)
        self.assertFalse(
            os.path.exists(path),
            "Picture has not been deleted by repository.remove_picture",
        )
        self.assertEqual(
            len(picture_group.locations["Temporary"]),
            location_initial_count - 1,
            "Picture has not been deleted from picture_group.locations",
        )
        self.assertEqual(
            len(picture_group.pictures[""]),
            conversion_type_initial_count - 1,
            "Picture has not been deleted from picture_group.pictures",
        )

        # Delete image while removing values from .pictures and .locations
        picture_group = repository.trips["Malta"]["IMG002"]
        picture = picture_group.pictures["DT"][0]
        path = picture.path
        repository.remove_picture(picture_group, picture)
        self.assertFalse(
            os.path.exists(path),
            "Picture has not been deleted by repository.remove_picture",
        )
        self.assertNotIn(
            "DT",
            picture_group.pictures,
            "picture_group.pictures still has DT as key",
        )
        self.assertNotIn(
            "Temporary",
            picture_group.locations,
            "picture_group.locations still has Temporary as key",
        )

        # Negative deletion test
        test_name = "Delete image from wrong group (based on trip)"
        picture_group = repository.trips["Malta"]["IMG002"]
        picture = repository.trips["Georgia"]["IMG010"]
        with self.assertRaises(ValueError) as cm:
            repository.remove_picture(picture_group, picture)
        self.assertEqual(type(cm.exception), ValueError, test_name)
        self.assertEqual(
            cm.exception.args[0],
            "Picture IMG010 has the wrong trip for group IMG002",
            test_name,
        )

    def test_group_name_change(self):
        # Load the pictures
        locations = self.database.storagelocations_get_folders()
        repository = Repository()
        repository.load_pictures(locations)

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
