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

logging.basicConfig(level=logging.CRITICAL)

DATABASE_FILE = "test.sqlite"
BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"
PICTURE_ZIP_FILE = os.path.join(BASE_DIR, "test_photos.zip")


class TestUiPictures:
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
            os.path.join(BASE_FOLDER, "DCIM", "IMG050.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "122_12", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "122_12", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "123__05", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "DCIM", "123__05", "IMG020.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG010_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG011_convert.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Korea", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Korea", "IMG030_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_RT.jpg"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002.CR2"),
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
                    command="cp %SOURCE_FILE% %TARGET_FILE%",
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
        # Setup: get display
        folders = self.database.storagelocations_get_folders()
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        # Check what happens when display is refreshed twice in a row
        picturesController.refresh_folders()
        foldersLayout = picturesController.ui["left_grid_layout"]

        # Check display - Overall structure
        assert (
            foldersLayout.columnCount() == 2
        ), "Folders display has the right number of colums"
        assert foldersLayout.rowCount() == len(
            folders
        ), "Folders display has the right number of rows"

        # Check display - Folder names
        name_label = foldersLayout.itemAtPosition(0, 0).widget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == folders[0].name
        ), "Name field displays the expected data"

        # Check display - Path display
        path_label = foldersLayout.itemAtPosition(0, 1).widget()
        assert isinstance(path_label, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_label.text() == folders[0].path
        ), "Path field displays the expected data"

    def test_pictures_load_pictures(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesController.refresh_display()
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)
        # Second time to test refresh of already-displayed data
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Check display - Tree has the right number of columns
        assert (
            picturesTree.columnCount() == 6
        ), "Picture tree has the right number of columns"

        # Check display - Tree has the right number of high-level items
        assert picturesTree.topLevelItemCount() == 7, "Found the right number of trips"

        # Check display - Malta's images
        malta = picturesTree.topLevelItem(5)
        malta_children = [malta.child(i).text(0) for i in range(malta.childCount())]
        assert malta.childCount() == 2, "Malta's children count is OK"
        assert malta_children == ["IMG001", "IMG002"], "Malta's children are OK"

    def test_pictures_tree_click_trip(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(1)  # Georgia
        topleft = picturesTree.visualItemRect(trip_item).topLeft()

        # Click on trip - should not display the picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - Grid should not be displayed
        assert picturesGrid.picture_group is None, "PictureGrid has no picture_group"
        assert picturesGrid.ui["layout"].columnCount() == 1, "PictureGrid is empty"
        assert picturesGrid.ui["layout"].rowCount() == 1, "PictureGrid is empty"
        assert (
            picturesGrid.ui["layout"].itemAtPosition(0, 0) is None
        ), "PictureGrid is empty"

    def test_pictures_tree_click_picture_group(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid (twice to check if it handles it well)
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - Overall grid structure
        assert picturesGrid.picture_group is not None, "PictureGrid has a picture_group"
        assert (
            picturesGrid.ui["layout"].columnCount() == 4
        ), "PictureGrid has right number of columns"
        assert (
            picturesGrid.ui["layout"].rowCount() == 6
        ), "PictureGrid has right number of rows"

        # Check display - Correct display of different images (RAW, JPG, no image)
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

    def test_pictures_tree_remove_already_removed_picture_group(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        # Should not trigger an error
        picturesTree.remove_picture_group(picture_item)
        picturesTree.remove_picture_group(picture_item)
        picturesTree.remove_picture_group(None)

    def test_pictures_grid_copy_raw_picture(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Georgia's IMG010
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = picturesController.repository.trips["Georgia"]["IMG010"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - No image displayed
        test = "Before RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "No image")
        copy = container.layout().itemAt(2).widget()

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=5000) as blocker:
            qtbot.mouseClick(copy, Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010.CR2")
        new_files = [new_path]
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]
        assert blocker.args[0].path == new_path, "Added picture signal has correct path"
        assert blocker.args[1] == "", "Added picture signal has empty conversion method"
        self.helper_check_paths("Copy RAW image", new_files)
        assert len(picture_group.pictures[""]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG010.CR2")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(0), "0 image in Archive"

    def test_pictures_grid_copy_jpg_picture(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Georgia's IMG010
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = picturesController.repository.trips["Georgia"]["IMG010"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - No image displayed
        test = "Before JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "No image")
        copy = container.layout().itemAt(2).widget()

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=5000) as signal:
            qtbot.mouseClick(copy, Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010_RT.jpg")
        new_files = [new_path]
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]
        assert signal.args[0].path == new_path, "Added picture signal has correct path"
        assert signal.args[1] == "RT", "Added picture signal has RT as conversion"
        self.helper_check_paths("Copy JPG image", new_files)
        assert len(picture_group.pictures["RT"]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG010_RT.jpg")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(0), "0 image in Archive"

    def test_pictures_grid_copy_error(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get Copy button
        container = picturesGrid.ui["layout"].itemAtPosition(2, 2).widget()
        copy = container.layout().itemAt(2).widget()

        # Trigger action - Should raise (caught) exception
        qtbot.mouseClick(copy, Qt.LeftButton)

        # Check display - Error is displayed
        error = container.layout().itemAt(3).widget()
        assert error.text() == "No source image found", "Error is displayed"

    def test_pictures_grid_delete_picture(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = picturesController.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )

        # Trigger action - 1 image deleted
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        delete = container.layout().itemAt(2).widget()
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=1000) as signal:
            qtbot.mouseClick(delete, Qt.LeftButton)

        # Check signal is emitted, file have been deleted & models updated
        deleted_path = os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG001_RT.jpg")
        deleted_files = [deleted_path]
        assert signal.args[0] == "RT", "Deletion signal has correct conversion type"
        assert (
            signal.args[1].name == "Temporary"
        ), "Deletion signal has correct location"
        self.helper_check_paths("Delete image", [], deleted_files)
        assert "RT" not in picture_group.pictures, "Picture deleted from group"

        # Check display - New image is displayed
        test = "After picture deletion"
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        self.helper_check_picture_display(test, container, "No image")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group.data(2, Qt.DisplayRole) == str(1), "1 images in Temporary"
        assert tree_group.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"

    def test_pictures_grid_convert_picture(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = picturesController.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Trigger action - 1 image deleted
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        generate = container.layout().itemAt(1).widget()
        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(generate, Qt.LeftButton)

        # Check signal is emitted, file have been deleted & models updated
        new_path = os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_DT.jpg")
        new_files = [new_path]
        assert signal.args[0].path == new_path, "New picture has correct path"
        assert signal.args[1] == "DT", "New picture has correct conversion method"
        self.helper_check_paths("Generated image", new_files)
        assert len(picture_group.pictures["DT"]) == 1, "Picture has 1 DT image"

        # Check display - New image is displayed
        test = "After picture generation"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        # This is called with "RAW" because the "conversion" is only a copy in this test
        self.helper_check_picture_display(test, container, "RAW", "IMG001_DT.jpg")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group.data(3, Qt.DisplayRole) == str(2), "2 image in Archive"

    def test_pictures_grid_convert_picture_no_method_found(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        picturesGrid = picturesController.ui["picture_grid"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(6)  # Sweden
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Sweden's IMG040
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get Copy button
        container = picturesGrid.ui["layout"].itemAtPosition(2, 4).widget()
        generate = container.layout().itemAt(1).widget()

        # Trigger action - Should raise (caught) exception
        qtbot.mouseClick(generate, Qt.LeftButton)

        # Check display - Error is displayed
        error = container.layout().itemAt(3).widget()
        assert error.text() == "No conversion method found", "Error is displayed"

    def test_pictures_tree_trip_copy(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip = picturesController.repository.trips["Georgia"]
        picture_group_010 = trip["IMG010"]
        picture_group_011 = trip["IMG011_convert"]

        # Look for copy action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu_actions if a.text() == action_name][0]

        # Trigger action - 3 images copied
        signals = [picture_group_010.pictureAdded] * 2 + [
            picture_group_011.pictureAdded
        ]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]
        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG010_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG011_convert.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            "Archive" in picture_group_010.locations
        ), "New location added to picture_group"
        assert (
            len(picture_group_010.locations["Archive"]) == 2
        ), "Archive has 2 IMG010 pictures"

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(2), "2 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"

    def test_pictures_tree_trip_convert(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_group1 = picturesController.repository.trips["Malta"]["IMG001"]
        picture_group2 = picturesController.repository.trips["Malta"]["IMG002"]

        # Look for generate action
        picturesTree.generate_context_menu(trip_item)
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        menu = [
            m
            for m in picturesTree.menu.children()
            if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
        ][0]
        action = [a for a in menu.actions() if a.text() == action_name][0]

        # Trigger action - 2 images converted
        signals = [picture_group1.pictureAdded, picture_group2.pictureAdded]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_DT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(menu_name + " " + action_name, new_files)
        assert (
            len(picture_group1.locations["Archive"]) == 2
        ), "Picture added to picture group"

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(2), "2 images in Archive"
        tree_group2 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG002"][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(2), "2 images in Archive"

    def test_pictures_tree_trip_change_name(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picture_group = picturesController.repository.trips["Korea"]["IMG030"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Change name to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )

        # Trigger action - 2 images moved
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Temporary", "Italy"),
            os.path.join(BASE_FOLDER, "Archive", "Italy"),
        ]
        new_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Italy", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Italy", "IMG030_RT.jpg"),
        ]
        removed_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Korea", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Korea", "IMG030_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)

        # Check display - Tree has been updated
        top_level_items = [
            picturesTree.topLevelItem(i).text(0)
            for i in range(picturesTree.topLevelItemCount())
        ]
        assert "Italy" in top_level_items, "Italy added to the tree"
        assert "Korea" not in top_level_items, "Korea removed from the tree"

    def test_pictures_tree_trip_change_name_exists(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picture_group = picturesController.repository.trips["Korea"]["IMG030"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Change name to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )

        # Trigger action - 2 images moved
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]
        new_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG030_RT.jpg"),
        ]
        removed_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Korea", "IMG030.CR2"),
            os.path.join(BASE_FOLDER, "Archive", "Korea", "IMG030_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)

        # Check display - Tree has been updated
        top_level_items = [
            picturesTree.topLevelItem(i).text(0)
            for i in range(picturesTree.topLevelItemCount())
        ]
        assert "Georgia" in top_level_items, "Georgia still in the tree"
        assert "Korea" not in top_level_items, "Korea removed from the tree"

    def test_pictures_tree_trip_wrong_action_name(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Trigger the addition of an impossible action
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picturesTree.generate_context_menu(trip_item)
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            picturesTree.add_trip_action("", "", action_name, "", "", "")

    def test_pictures_tree_picture_group_copy(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(0)  # Malta's IMG001
        picture_group = picturesController.repository.trips["Malta"]["IMG001"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG001 pictures"

        # Check display - Tree has been updated
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(2), "2 image in Archive"

    def test_pictures_tree_picture_group_convert(self, qtbot):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = picturesController.repository.trips["Malta"]["IMG002"]

        # Look for convert action
        picturesTree.generate_context_menu(picture_item)
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        menu = [
            m
            for m in picturesTree.menu.children()
            if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
        ][0]
        action = [a for a in menu.actions() if a.text() == action_name][0]

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG002 pictures"

        # Check display - Tree has been updated
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(2), "2 image in Archive"

    def test_pictures_tree_picture_group_change_trip(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = picturesController.repository.trips["Malta"]["IMG002"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Change trip to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Temporary", "Italy"),
            os.path.join(BASE_FOLDER, "Archive", "Italy"),
        ]
        new_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Italy", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Italy", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Italy", "IMG002.CR2"),
        ]
        removed_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002.CR2"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)
        picture_group = picturesController.repository.trips["Italy"]["IMG002"]
        assert (
            len(picture_group.locations["Archive"]) == 1
        ), "Archive has 1 IMG002 picture"

        # Check display - Tree has been updated
        italy_item = [
            picturesTree.topLevelItem(i)
            for i in range(picturesTree.topLevelItemCount())
            if picturesTree.topLevelItem(i).text(0) == "Italy"
        ][0]
        picture_item = italy_item.child(0)
        assert italy_item.data(0, Qt.DisplayRole) == "Italy", "New trip displayed"
        assert picture_item.data(0, Qt.DisplayRole) == "IMG002", "New picture displayed"
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"

    def test_pictures_tree_picture_group_change_trip_target_exists(
        self, qtbot, monkeypatch
    ):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = picturesController.repository.trips["Malta"]["IMG002"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Change trip to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        self.all_folders += [
            os.path.join(BASE_FOLDER, "Temporary", "Georgia"),
            os.path.join(BASE_FOLDER, "Archive", "Georgia"),
        ]
        new_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Georgia", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Georgia", "IMG002.CR2"),
        ]
        removed_files = [
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002.CR2"),
            os.path.join(BASE_FOLDER, "Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join(BASE_FOLDER, "Archive", "Malta", "IMG002.CR2"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)
        picture_group = picturesController.repository.trips["Georgia"]["IMG002"]
        assert (
            len(picture_group.locations["Archive"]) == 1
        ), "Archive has 1 IMG002 picture"

        # Check display - Tree has been updated
        italy_item = [
            picturesTree.topLevelItem(i)
            for i in range(picturesTree.topLevelItemCount())
            if picturesTree.topLevelItem(i).text(0) == "Georgia"
        ][0]
        picture_item = [
            italy_item.child(i)
            for i in range(italy_item.childCount())
            if italy_item.child(i).data(0, Qt.DisplayRole) == "IMG002"
        ][0]
        assert italy_item.data(0, Qt.DisplayRole) == "Georgia", "New trip displayed"
        assert picture_item.data(0, Qt.DisplayRole) == "IMG002", "New picture displayed"
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"

    def test_pictures_tree_picture_group_wrong_action_name(self, qtbot, monkeypatch):
        # Setup: get display, load pictures
        self.mainwindow.display_tab("Pictures")
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesTree = picturesController.ui["picture_tree"]
        load_pictures_button = picturesController.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Trigger the addition of an impossible action
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picturesTree.generate_context_menu(picture_item)
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            picturesTree.add_picture_group_action("", "", action_name, "", "", "")


if __name__ == "__main__":
    pytest.main(["-s", "--tb=line", __file__])
