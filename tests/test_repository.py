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
            BASE_FOLDER + "Temporary/",
            BASE_FOLDER + "Temporary/Malta/",
            BASE_FOLDER + "Temporary/Georgia/",
            BASE_FOLDER + "Temporary/Korea/",
            BASE_FOLDER + "Archive/",
            BASE_FOLDER + "Archive/Malta/",
            BASE_FOLDER + "Archive/Korea/",
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
            BASE_FOLDER + "Temporary/Malta/IMG001_RT.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG002_RT.CR2",
            BASE_FOLDER + "Archive/Malta/IMG001.CR2",
            BASE_FOLDER + "Archive/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010_RT.jpg",
            BASE_FOLDER + "Temporary/Georgia/IMG011_convert.jpg",
            BASE_FOLDER + "Temporary/Korea/IMG030.CR2",
            BASE_FOLDER + "Archive/Korea/IMG030_RT.CR2",
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
        self.assertEqual(len(self.repository.trips), 4, test)

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
        new_location = StorageLocation(
            id=999,
            name="Outside_DB",
            type="folder",
            path=BASE_FOLDER + "Archive_outside_DB/",
        )
        self.repository.load_pictures([new_location])
        test = "Add a storage location: Count trips"
        self.assertEqual(len(self.repository.trips), 5, test)

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

    def test_picture_group_remove_picture_actual_deletion(self):
        # Delete image without changing structure of .pictures and .locations
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        location_initial_count = len(picture_group.locations["Temporary"])
        conversion_type_initial_count = len(picture_group.pictures[""])
        path = picture.path
        process = self.repository.remove_pictures("", None, picture_group, picture)
        process.finished.connect(
            lambda: self.assertFalse(
                os.path.exists(path),
                "Remove picture : deletion by self.repository.remove_picture",
            )
        )
        process.finished.connect(
            lambda: self.assertEqual(
                len(picture_group.locations["Temporary"]),
                location_initial_count - 1,
                "Remove picture : deletion from picture_group.locations",
            )
        )
        process.finished.connect(
            lambda: self.assertEqual(
                len(picture_group.pictures[""]),
                conversion_type_initial_count - 1,
                "Remove picture : deletion from picture_group.pictures",
            )
        )

    def test_picture_group_remove_picture_no_structure_change(self):
        # Remove image without deleting the actual files
        # This is because coverage doesn't realize it has been tested indirectly
        # The keys of .pictures and .locations are preserved
        picture_group = self.repository.trips["Malta"]["IMG002"]
        picture = picture_group.locations["Temporary"][0]
        location_initial_count = len(picture_group.locations["Temporary"])
        conversion_type_initial_count = len(picture_group.pictures[""])
        path = picture.path
        picture_group.remove_picture(picture)
        self.assertTrue(
            os.path.exists(path),
            "Remove picture : file not deleted (on purpose)",
        )
        self.assertEqual(
            len(picture_group.locations["Temporary"]),
            location_initial_count - 1,
            "Remove picture : deletion from picture_group.locations",
        )
        self.assertEqual(
            len(picture_group.pictures[""]),
            conversion_type_initial_count - 1,
            "Remove picture : deletion from picture_group.pictures",
        )

    def test_picture_group_remove_picture_structure_change(self):
        # Remove image without deleting the actual files
        # This is because coverage doesn't realize it has been tested indirectly
        # The keys of .pictures and .locations are changed
        picture_group = self.repository.trips["Korea"]["IMG030"]
        picture = picture_group.pictures["RT"][0]
        path = picture.path
        picture_group.remove_picture(picture)
        self.assertTrue(
            os.path.exists(path),
            "Remove picture : file not deleted (on purpose)",
        )
        self.assertNotIn(
            "RT",
            picture_group.pictures,
            "picture_group.pictures no longer has 'RT' as key",
        )
        self.assertNotIn(
            "Archive",
            picture_group.locations,
            "picture_group.locations no longer has Archive as key",
        )

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

    def test_group_name_change(self):
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
