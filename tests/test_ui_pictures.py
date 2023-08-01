import os
import sys
import pytest
import datetime
import logging
import zipfile
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import models.database as databasemodel
import controllers.mainwindow
from controllers.pictures import PictureDisplay
from controllers.widgets.iconbutton import IconButton

from models.storagelocation import StorageLocation
from models.storagelocation import StorageLocationType
from models.conversionmethod import ConversionMethod

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"
PICTURE_ZIP_FILE = os.path.join(BASE_DIR, "test_photos.zip")


class TestUiSettings:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self, qtbot):
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
        with zipfile.ZipFile(PICTURE_ZIP_FILE, "r") as zip_ref:
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

        self.mainwindow = controllers.mainwindow.MainWindow(self.database)

        yield

        self.mainwindow.database.session.close()
        self.mainwindow.database.engine.dispose()
        # Delete database
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
                assert os.path.exists(path), f"{test} - File {path}"
            else:
                assert not os.path.exists(path), f"{test} - File {path}"

    def helper_check_picture_display(self, test, container, display_type, path=None):
        if display_type == "JPG":
            assert container.layout().count() == 3, test + " : 3 items displayed"
            filename = container.layout().itemAt(0).widget()
            picture = container.layout().itemAt(1).widget()
            delete = container.layout().itemAt(2).widget()
            assert filename.text() == path, test + " : filename display"
            assert isinstance(picture, PictureDisplay), test + " : image display"
            assert isinstance(delete, IconButton), test + " : delete display"
        elif display_type == "RAW":
            assert container.layout().count() == 2, test + " : 2 items displayed"
            filename = container.layout().itemAt(0).widget()
            picture = container.layout().itemAt(1).widget()
            assert filename.text() == path, test + " : filename display"
            assert picture.text() == "Image unreadable", test + " : image display"
        elif display_type == "No image":
            assert container.layout().count() == 3, test + " : 3 items displayed"
            label = container.layout().itemAt(0).widget()
            generate = container.layout().itemAt(1).widget()
            copy = container.layout().itemAt(2).widget()
            assert label.text() == "No image", test + " : label display"
            assert generate.text() == "Generate", test + " : generate display"
            assert copy.text() == "Copy image here", test + " : copy display"
        else:
            raise ValueError("display_type should be RAW, JPG or No image")

    def test_pictures_folders_display(self):
        folders = self.database.storagelocations_get_folders()
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesController.refresh_folders()
        foldersLayout = picturesController.ui["left_grid_layout"]

        # Check overall structure
        assert (
            foldersLayout.columnCount() == 2
        ), "Folders display has the right number of colums"
        assert foldersLayout.rowCount() == len(
            folders
        ), "Folders display has the right number of rows"

        # Check name display
        name_label = foldersLayout.itemAtPosition(0, 0).widget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == folders[0].name
        ), "Name field displays the expected data"

        # Check path display
        path_label = foldersLayout.itemAtPosition(0, 1).widget()
        assert isinstance(path_label, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_label.text() == folders[0].path
        ), "Path field displays the expected data"

    def test_pictures_load_pictures(self, qtbot):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesController.refresh_display()

        # Check overall structure
        assert (
            picturesTree.columnCount() == 6
        ), "Picture tree has the right number of columns"

        # Trigger load of pictures
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Check tree top level items
        assert picturesTree.topLevelItemCount() == 7, "Found the right number of trips"

        # Check Malta's images
        malta = picturesTree.topLevelItem(5)
        assert malta.childCount() == 2, "Malta's children count is OK"
        malta_children = [malta.child(i).text(0) for i in range(malta.childCount())]
        assert malta_children == ["IMG001", "IMG002"], "Malta's children are OK"

    def test_pictures_tree_click_trip(self, qtbot):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        picturesController.refresh_display()

        # Trigger load of pictures
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Click on a trip (Georgia, should do nothing)
        trip_item = picturesTree.topLevelItem(1)
        topleft = picturesTree.visualItemRect(trip_item).topLeft()
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        # Check results
        assert picturesGrid.picture_group is None, "PictureGrid has no picture_group"

    def test_pictures_tree_click_picture_group(self, qtbot):
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        picturesController.refresh_display()

        # Load pictures
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Click on a picture group (Malta's IMG001)
        trip_item = picturesTree.topLevelItem(5)
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check overall structure
        assert picturesGrid.picture_group is not None, "PictureGrid has a picture_group"
        assert (
            picturesGrid.ui["layout"].columnCount() == 4
        ), "PictureGrid has right number of columns"
        assert (
            picturesGrid.ui["layout"].rowCount() == 6
        ), "PictureGrid has right number of rows"

        # Check right picture is displayed in each box
        # "No image"
        test = "No image"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        self.helper_check_picture_display(test, container, "No image")

        # RAW image ==> readable
        test = "RAW image"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG001.CR2")

        # JPG image ==> readable
        test = "JPG image"
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG001_RT.jpg")

    def test_pictures_tree_copy_raw_individual_picture(self, qtbot):
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        picturesController.refresh_display()

        # Load pictures
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Click on a picture group (Georgia's IMG010)
        trip_item = picturesTree.topLevelItem(3)
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        picture_group = picturesGrid.picture_group

        # New folder will get added
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]

        # No image displayed before
        test = "Before RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "No image")
        copy = container.layout().itemAt(2).widget()

        # Wait and check the signal is emitted
        new_path = os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010.CR2")
        new_files = [new_path]
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=5000) as blocker:
            qtbot.mouseClick(copy, Qt.LeftButton)
        assert blocker.args[0].path == new_path, "Added picture signal has correct path"
        assert blocker.args[1] == "", "Added picture signal has empty conversion method"

        # Files & models are updated
        self.helper_check_paths("Copy RAW image", new_files)
        assert len(picture_group.pictures[""]) == 2, "New picture in group"

        # New image displayed properly
        test = "After RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG010.CR2")

    def test_pictures_tree_copy_jpg_individual_picture(self, qtbot):
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        picturesController.refresh_display()

        # Load pictures
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Click on a picture group (Georgia's IMG010)
        trip_item = picturesTree.topLevelItem(3)
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        picture_group = picturesGrid.picture_group

        # New folder will get added
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]

        # No image displayed before
        test = "Before JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "No image")
        copy = container.layout().itemAt(2).widget()

        # Wait and check the signal is emitted
        new_path = os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010_RT.jpg")
        new_files = [new_path]
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=5000) as blocker:
            qtbot.mouseClick(copy, Qt.LeftButton)
        assert blocker.args[0].path == new_path, "Added picture signal has correct path"
        assert (
            blocker.args[1] == "RT"
        ), "Added picture signal has empty conversion method"

        # Files & models are updated
        self.helper_check_paths("Copy JPG image", new_files)
        assert len(picture_group.pictures["RT"]) == 2, "New picture in group"

        # New image displayed properly
        test = "After JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG010_RT.jpg")

    def _test(self):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesGrid = picturesController.ui["picture_grid"]
        picturesController.refresh_display()
        for row in range(picturesGrid.ui["layout"].rowCount()):
            for col in range(picturesGrid.ui["layout"].columnCount()):
                container = picturesGrid.ui["layout"].itemAtPosition(row, col).widget()
                if not container.layout():
                    print(row, col, container.text(), "label")
                else:
                    print(
                        row, col, container.layout().itemAt(0).widget().text(), "cont"
                    )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
