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
            BASE_FOLDER + "DCIM/IMG011.CR2",
            BASE_FOLDER + "DCIM/IMG020.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG001.CR2",
            BASE_FOLDER + "Temporary/Malta/IMG002.CR2",
            BASE_FOLDER + "Archive/Malta/IMG001.CR2",
            BASE_FOLDER + "Archive/Malta/IMG002.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG010.CR2",
            BASE_FOLDER + "Temporary/Georgia/IMG011.CR2",
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

    def test_pictures(self):
        # Identify all pictures
        storage_locations = self.database.storagelocations_get_folders()
        locations = {loc.name: loc.path for loc in storage_locations}
        repository = Repository(locations)
        repository.load_pictures()

        self.assertEqual(
            len(repository.trips),
            3,
            "There are 3 trips",
        )
        self.assertEqual(
            len(repository.trips[""]),
            5,
            "There are 5 pictures with no trip",
        )
        self.assertEqual(
            len(repository.trips["Malta"]),
            4,
            "There are 4 pictures in the Malta trip",
        )

        repository.load_pictures({"Outside_DB": BASE_FOLDER + "Archive_outside_DB/"})
        self.assertEqual(
            len(repository.trips),
            4,
            "There are 4 trips",
        )

        picture = [
            p for p in repository.trips["Malta"] if p.path.endswith("IMG001.CR2")
        ]
        picture = picture[0]
        self.assertEqual(
            str(picture),
            "('IMG001.CR2', 'Malta', 'Temporary', '"
            + BASE_FOLDER
            + "Temporary/Malta/IMG001.CR2')",
            "String representation of a picture: name, trip, folder name, path",
        )

        with self.assertRaises(StorageLocationCollision):
            repository.load_pictures({"Used path": BASE_FOLDER + "Temporary/Malta"})
