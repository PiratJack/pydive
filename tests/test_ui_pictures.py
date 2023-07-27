import os
import sys
import unittest
import datetime
import logging
from PyQt5 import QtWidgets, QtTest
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database as databasemodel
import controllers.mainwindow
import controllers.widgets.iconbutton
import controllers.widgets.pathselectbutton

from models.storagelocation import StorageLocation
from models.storagelocation import StorageLocationType
from models.conversionmethod import ConversionMethod

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"


class TestUiSettings(unittest.TestCase):
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
            os.path.join(BASE_FOLDER, "DCIM", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "IMG020.CR2"),
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
                    command="../../pydive_generate_picture.py %SOURCE_FILE% -t %TARGET_FOLDER% -c DT",
                ),
                ConversionMethod(
                    id=2,
                    name="RawTherapee",
                    suffix="RT",
                    command="../../pydive_generate_picture.py %SOURCE_FILE% -t %TARGET_FOLDER% -c RT",
                ),
            ]
        )
        self.database.session.commit()
        self.database.session.close()
        self.database.engine.dispose()

        if sys.platform == "linux":
            os.environ["QT_QPA_PLATFORM"] = "xcb"
        self.app = QtWidgets.QApplication(sys.argv)
        self.mainwindow = controllers.mainwindow.MainWindow(self.database)

    def tearDown(self):
        self.mainwindow.close()
        self.mainwindow.database.session.close()
        self.mainwindow.database.engine.dispose()
        self.app.quit()
        # Delete database
        os.remove(DATABASE_FILE)

        # Delete folders
        for test_file in self.all_files:
            if os.path.exists(test_file):
                os.remove(test_file)
        for folder in sorted(self.all_folders, reverse=True):
            os.rmdir(folder)

    def test_pictures_folders_display(self):
        folders = self.database.storagelocations_get_folders()
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesController.refresh_folders()
        foldersLayout = picturesController.ui["left_grid_layout"]

        # Check overall structure
        self.assertEqual(
            foldersLayout.columnCount(),
            2,
            "Folders display has the right number of colums",
        )
        self.assertEqual(
            foldersLayout.rowCount(),
            len(folders),
            "Folders display has the right number of rows",
        )

        # Check name display
        name_label = foldersLayout.itemAtPosition(0, 0).widget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEqual(
            name_label.text(), folders[0].name, "Name field displays the expected data"
        )

        # Check path display
        path_label = foldersLayout.itemAtPosition(0, 1).widget()
        self.assertTrue(
            isinstance(path_label, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEqual(
            path_label.text(), folders[0].path, "Path field displays the expected data"
        )

    def test_pictures_load_pictures(self):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesController.refresh_display()

        # Check overall structure
        self.assertEqual(
            picturesTree.columnCount(),
            6,
            "Picture tree has the right number of columns",
        )

        # Trigger load of pictures
        load_pictures_button = picturesController.ui["load_button"]
        QtTest.QTest.mouseClick(load_pictures_button, Qt.LeftButton)

        # Check tree top level items
        self.assertEqual(
            picturesTree.topLevelItemCount(), 5, "Found the right number of trips"
        )

        # Check Malta's images
        malta = picturesTree.topLevelItem(3)
        self.assertEqual(malta.childCount(), 2, "Malta's children count is OK")
        malta_children = [malta.child(i).text(0) for i in range(malta.childCount())]
        self.assertEqual(
            malta_children, ["IMG001", "IMG002"], "Malta's children are OK"
        )


if __name__ == "__main__":
    unittest.main()
