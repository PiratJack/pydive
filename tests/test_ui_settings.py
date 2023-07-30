import os
import sys
import unittest
import datetime
import logging
from PyQt5 import QtWidgets, QtTest, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.database as databasemodel
import controllers.mainwindow
from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.iconbutton import IconButton

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
        self.app.deleteLater()
        # ## Delete database
        os.remove(DATABASE_FILE)

        # ## Delete folders
        for test_file in self.all_files:
            if os.path.exists(test_file):
                os.remove(test_file)
        for folder in sorted(self.all_folders, reverse=True):
            os.rmdir(folder)

    def test_settings_location_list_display(self):
        location = self.database.storagelocation_get_by_id(1)
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Check overall structure
        self.assertEqual(
            locationList.location_type, "folder", "Location list displays folders"
        )

        self.assertEqual(
            locationList.ui["layout"].columnCount(),
            5,
            "Locations have the right number of colums",
        )
        self.assertEqual(
            locationList.ui["layout"].rowCount(),
            7,
            "Locations have the right number of rows",
        )

        # Check name display
        name_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        )
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEqual(
            name_label.text(), location.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = locationList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_name_button, IconButton),
            "Change name button is a IconButton",
        )

        # Check path display
        path_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        )
        path_widget = path_wrapper_layout.itemAt(0).widget()
        self.assertTrue(
            isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEqual(
            path_widget.text(), location.path, "Path field displays the expected data"
        )

        # Check "change path" display
        change_path_widget = locationList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertTrue(
            isinstance(change_path_widget, PathSelectButton),
            "Change path button is a PathSelectButton",
        )

        # Check Delete display
        delete_widget = locationList.ui["layout"].itemAtPosition(1, 4).widget()
        self.assertTrue(
            isinstance(delete_widget, IconButton),
            "Delete button is a IconButton",
        )

        # Check "Add new" display
        add_new_widget = locationList.ui["layout"].itemAtPosition(6, 1).widget()
        self.assertEqual(
            add_new_widget.__class__.__name__,
            "IconButton",
            "Add new button is a IconButton",
        )

    def test_settings_location_list_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get name-related widgets
        name_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        )
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = (
            locationList.ui["layout"].itemAtPosition(1, 1).widget().layout()
        )
        name_change_start = name_change_layout.currentWidget()

        # Check "name change start" receivers
        self.assertEqual(name_change_start.receivers(name_change_start.clicked), 1)
        name_change_start_signalspy = QtTest.QSignalSpy(name_change_start.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(name_change_start, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_start_signalspy.isValid(), "Name change start signal is emitted"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the storage location
        name_edit = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEqual(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the location's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEqual(
            name_change_start, name_change_end, "Edit button replaced by Save button"
        )

        # Check "name change end" receivers
        self.assertEqual(name_change_end.receivers(name_change_end.clicked), 1)
        name_change_end_signalspy = QtTest.QSignalSpy(name_change_end.clicked)

        # Change the name in UI & save changes
        name_edit.setText("SD Card")
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_end_signalspy.isValid(), "Name change end signal is emitted"
        )
        self.assertEqual(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        location = self.database.storagelocation_get_by_id(1)
        self.assertEqual(location.name, "SD Card", "Name is updated in database")

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        self.assertEqual(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEqual(name_label.text(), "SD Card", "Name is updated on display")

        name_change_widget = name_change_layout.currentWidget()
        self.assertEqual(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_location_list_edit_name_error(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get name-related widgets
        name_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        )
        name_change_layout = (
            locationList.ui["layout"].itemAtPosition(1, 1).widget().layout()
        )
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        QtTest.QTest.mouseClick(name_change_start, Qt.LeftButton)

        # Change the name
        name_edit = name_wrapper_layout.itemAt(0).widget().layout().currentWidget()
        name_edit.setText("")

        # Save changes
        name_change_end = name_change_layout.currentWidget()
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)
        # Triggered twice to test when errors were displayed before
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)

        # Check error is displayed
        error_widget = name_wrapper_layout.itemAt(1).widget()
        self.assertEqual(
            error_widget.text(), "Missing storage location name", "Error gets displayed"
        )

        # Changes are not saved in DB
        location = self.database.storagelocation_get_by_id(1)
        self.assertNotEqual(location.name, "", "Name is not modified to empty")

    def test_settings_location_list_edit_path(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get change path button
        change_path_widget = locationList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertEqual(
            change_path_widget.target_type, "folder", "Path change looks for folders"
        )

        # Check event receivers
        self.assertEqual(
            change_path_widget.receivers(change_path_widget.pathSelected), 1
        )
        path_change_signalspy = QtTest.QSignalSpy(change_path_widget.pathSelected)

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("This is a new path")

        # Check signal is emitted
        self.assertTrue(
            path_change_signalspy.isValid(), "Path change signal is emitted"
        )
        self.assertEqual(
            len(path_change_signalspy), 1, "Path change signal is emitted once"
        )
        self.assertEqual(
            path_change_signalspy[0],
            ["This is a new path"],
            "Path change signal has the correct data",
        )

        # Changes are saved in DB
        location = self.database.storagelocation_get_by_id(1)
        self.assertEqual(
            location.path,
            os.path.join("This is a new path", ""),
            "Path is updated in database",
        )

        # New path is displayed
        path_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        )
        path_widget = path_wrapper_layout.itemAt(0).widget()
        self.assertEqual(
            path_widget.text(), "This is a new path", "Path is updated on display"
        )

    def test_settings_location_list_edit_path_error(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get change path button
        change_path_widget = locationList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertEqual(change_path_widget.target_type, "folder")

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("")

        # Error message is displayed
        path_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        )
        error_widget = path_wrapper_layout.itemAt(1).widget()
        self.assertEqual(
            error_widget.text(), "Missing storage location path", "Error gets displayed"
        )

    @unittest.skip(
        "TODO Does not work, either does not trigger or qMessageBox not displayed"
    )
    def test_settings_location_list_delete_cancel(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get delete button
        delete_widget = locationList.ui["layout"].itemAtPosition(1, 4).widget()

        # Check there is no change in DB
        def check_location_exists():
            messagebox = self.app.activeModalWidget()
            QtTest.QTest.mouseClick(
                messagebox.button(QtWidgets.QMessageBox.No), Qt.LeftButton
            )

            location = self.database.storagelocation_get_by_id(1)
            self.assertEqual(location.name, "Camera", "Location still exists")

        # Click delete, then "No" in the dialog
        timer = QtCore.QTimer(self.mainwindow)
        timer.timeout.connect(check_location_exists)
        timer.start(100)
        QtTest.QTest.mouseClick(delete_widget, Qt.LeftButton)

    @unittest.skip(
        "TODO Does not work, triggers with same callback twice + the Yes button is not really triggered"
    )
    def test_settings_location_list_delete_confirm(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get delete button
        delete_widget = locationList.ui["layout"].itemAtPosition(2, 4).widget()

        def check_location_deleted():
            messagebox = self.app.activeModalWidget()
            QtTest.QTest.mouseClick(
                messagebox.button(QtWidgets.QMessageBox.Yes), Qt.LeftButton
            )

            # Check the DB has been updated
            location = self.database.storagelocation_get_by_id(2)
            self.assertEqual(location, None, "Location has been deleted")

            # Location no longer visible in UI
            self.assertEqual(
                locationList.ui["layout"].rowCount(),
                5,
                "Locations have the right number of rows",
            )
            self.assertEqual(
                locationList.ui["layout"].rowCount(),
                5,
                "Locations have the right number of rows",
            )

        # Click delete, then "Yes" in the dialog
        timer2 = QtCore.QTimer(settingsController.ui["main"])
        timer2.timeout.connect(check_location_deleted)
        timer2.start(300)
        QtTest.QTest.mouseClick(delete_widget, Qt.LeftButton)

    def test_settings_location_list_add_location_display(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get "add new" button
        add_new = locationList.ui["layout"].itemAtPosition(6, 1).widget()

        # Check "add new" receivers
        self.assertEqual(add_new.receivers(add_new.clicked), 1)
        add_new_signalspy = QtTest.QSignalSpy(add_new.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(add_new_signalspy.isValid(), "Add new signal is emitted")
        self.assertEqual(
            len(add_new_signalspy),
            1,
            "Add new signal is emitted once",
        )

        # New fields are now displayed
        name_wrapper = locationList.ui["layout"].itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLineEdit),
            "Add new - name is a QLineEdit",
        )
        self.assertEqual(
            name_label.text(),
            "",
            "Add new - name field is empty",
        )

        path_wrapper = locationList.ui["layout"].itemAtPosition(6, 2).widget().layout()
        path_label = path_wrapper.itemAt(0).widget()
        self.assertTrue(
            isinstance(path_label, QtWidgets.QLineEdit),
            "Add new - path is a QLineEdit",
        )
        self.assertEqual(
            path_label.text(),
            "",
            "Add new - path field is empty",
        )

        path_change = locationList.ui["layout"].itemAtPosition(6, 3).widget()
        self.assertTrue(
            isinstance(path_change, IconButton),
            "Add new - path change is an IconButton",
        )

    def test_settings_location_list_add_location_save(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get "add new" button
        add_new = locationList.ui["layout"].itemAtPosition(6, 1).widget()

        # Display edit fields
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # Enter a new name
        name_wrapper = locationList.ui["layout"].itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()

        name_label.setText("New location")

        # Enter a new path
        path_change = locationList.ui["layout"].itemAtPosition(6, 3).widget()
        self.assertEqual(
            path_change.target_type, "folder", "Path change looks for folders"
        )
        # Simulating the actual dialog is impossible (it's OS-provided)
        path_change.pathSelected.emit("New path")

        # Save changes
        save_button = locationList.ui["layout"].itemAtPosition(6, 4).widget()
        self.assertTrue(
            isinstance(save_button, IconButton), "Save button is an IconButton"
        )
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        # Data is saved in DB
        location = self.database.storagelocation_get_by_name("New location")
        self.assertEqual(location.name, "New location", "Name is saved in database")
        self.assertEqual(
            location.path, "New path" + os.path.sep, "Path is saved in database"
        )
        self.assertEqual(
            location.type.value["name"], "folder", "Location type is saved in database"
        )

        # Display is now similar as other locations
        self.assertEqual(locationList.ui["layout"].rowCount(), 8, "New line is added")
        # Check name display
        name_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(6, 0).widget().layout()
        )

        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEqual(
            name_label.text(), location.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = locationList.ui["layout"].itemAtPosition(6, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_name_button, IconButton),
            "Change name button is a IconButton",
        )

        # Check path display
        path_wrapper_layout = (
            locationList.ui["layout"].itemAtPosition(6, 2).widget().layout()
        )
        path_widget = path_wrapper_layout.itemAt(0).widget()
        self.assertTrue(
            isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEqual(
            path_widget.text(), location.path, "Path field displays the expected data"
        )

        # Check "change path" display
        change_path_widget = locationList.ui["layout"].itemAtPosition(6, 3).widget()
        self.assertTrue(
            isinstance(change_path_widget, PathSelectButton),
            "Change path button is a PathSelectButton",
        )

        # Check Delete display
        delete_widget = locationList.ui["layout"].itemAtPosition(6, 4).widget()
        self.assertTrue(
            isinstance(delete_widget, IconButton),
            "Delete button is a IconButton",
        )

    def test_settings_location_list_add_new_twice(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get "add new" button
        add_new = locationList.ui["layout"].itemAtPosition(6, 1).widget()

        # Display edit fields
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # "New location" fields are visible only once
        self.assertEqual(
            locationList.ui["layout"].rowCount(), 8, "Only 1 line is added"
        )

    def test_settings_location_list_add_with_errors(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Click "Add new"
        add_new = locationList.ui["layout"].itemAtPosition(6, 1).widget()
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = locationList.ui["layout"].itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        path_wrapper = locationList.ui["layout"].itemAtPosition(6, 2).widget().layout()
        path_change = locationList.ui["layout"].itemAtPosition(6, 3).widget()
        save_button = locationList.ui["layout"].itemAtPosition(6, 4).widget()

        # Save with blank fields & check errors
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNotNone(name_wrapper.itemAt(1), "Name error is displayed")
        name_error = name_wrapper.itemAt(1).widget()
        self.assertEqual(
            name_error.text(),
            "Missing storage location name",
            "Name error displays correct error",
        )

        self.assertIsNotNone(path_wrapper.itemAt(1), "Path error is displayed")
        path_error = path_wrapper.itemAt(1).widget()
        self.assertEqual(
            path_error.text(),
            "Missing storage location path",
            "Path error displays correct error",
        )

        # Click "Add new", all errors should be hidden
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)
        name_wrapper = locationList.ui["layout"].itemAtPosition(6, 0).widget().layout()
        path_wrapper = locationList.ui["layout"].itemAtPosition(6, 2).widget().layout()
        path_change = locationList.ui["layout"].itemAtPosition(6, 3).widget()
        save_button = locationList.ui["layout"].itemAtPosition(6, 4).widget()

        self.assertIsNone(name_wrapper.itemAt(1), "Name error is hidden")
        self.assertIsNone(path_wrapper.itemAt(1), "Path error is hidden")

        # Enter name, check error is hidden now
        name_label = name_wrapper.itemAt(0).widget()
        name_label.setText("New location")
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNone(name_wrapper.itemAt(1), "Name error is hidden")

        self.assertIsNotNone(path_wrapper.itemAt(1), "Path error is displayed")
        path_error = path_wrapper.itemAt(1).widget()
        self.assertEqual(
            path_error.text(),
            "Missing storage location path",
            "Path error displays correct error",
        )

        # Enter path, empty name, check error is hidden now
        path_change.pathSelected.emit("New path")
        name_label.setText("")
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNotNone(name_wrapper.itemAt(1), "Name error is displayed")
        name_error = name_wrapper.itemAt(1).widget()
        self.assertEqual(
            name_error.text(),
            "Missing storage location name",
            "Name error displays correct error",
        )

        self.assertIsNone(path_wrapper.itemAt(1), "Path error is hidden")

    def test_settings_divelog_display(self):
        divelog = self.database.storagelocation_get_by_id(6)
        settingsController = self.mainwindow.controllers["Settings"]
        divelogList = settingsController.divelog_list

        # Check overall structure
        self.assertEqual(
            divelogList.location_type, "file", "Dive log list displays files"
        )

        self.assertEqual(
            divelogList.ui["layout"].columnCount(),
            5,
            "Dive log display has the right number of colums",
        )
        self.assertEqual(
            divelogList.ui["layout"].rowCount(),
            2,
            "Dive log display has the right number of rows",
        )

        # Check name display
        name_wrapper_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        )
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEqual(
            name_label.text(), divelog.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = divelogList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_name_button, IconButton),
            "Change name button is a IconButton",
        )

        # Check path display
        path_wrapper_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        )
        path_widget = path_wrapper_layout.itemAt(0).widget()
        self.assertTrue(
            isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEqual(
            path_widget.text(), divelog.path, "Path field displays the expected data"
        )

        # Check "change path" display
        change_path_widget = divelogList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertTrue(
            isinstance(change_path_widget, PathSelectButton),
            "Change path button is a PathSelectButton",
        )

        # Check Delete display
        delete_widget = divelogList.ui["layout"].itemAtPosition(1, 4)
        self.assertEqual(delete_widget, None, "Impossible to delete divelog file")

    def test_settings_divelog_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        divelogList = settingsController.divelog_list

        # Get name-related widgets
        name_wrapper_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        )
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 1).widget().layout()
        )
        name_change_start = name_change_layout.currentWidget()
        self.assertTrue(
            isinstance(name_change_start, IconButton),
            "Name change button is a IconButton",
        )

        # Check "name change start" receivers
        self.assertEqual(name_change_start.receivers(name_change_start.clicked), 1)
        name_change_start_signalspy = QtTest.QSignalSpy(name_change_start.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(name_change_start, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_start_signalspy.isValid(), "Name change start signal is emitted"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the dive log
        name_edit = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEqual(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the dive log's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEqual(
            name_change_start, name_change_end, "Edit button replaced by Save button"
        )

        # Check "name change end" receivers
        self.assertEqual(name_change_end.receivers(name_change_end.clicked), 1)
        name_change_end_signalspy = QtTest.QSignalSpy(name_change_end.clicked)

        # Change the name in UI & save changes
        name_edit.setText("Subsurface file")
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_end_signalspy.isValid(), "Name change end signal is emitted"
        )
        self.assertEqual(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        divelog = self.database.storagelocation_get_by_id(6)
        self.assertEqual(divelog.name, "Subsurface file", "Name is updated in database")

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        self.assertEqual(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEqual(
            name_label.text(), "Subsurface file", "Name is updated on display"
        )

        name_change_widget = name_change_layout.currentWidget()
        self.assertEqual(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_divelog_edit_path(self):
        settingsController = self.mainwindow.controllers["Settings"]
        divelogList = settingsController.divelog_list

        # Get change path button
        change_path_widget = divelogList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertEqual(change_path_widget.target_type, "file")

        # Check event receivers
        self.assertEqual(
            change_path_widget.receivers(change_path_widget.pathSelected), 1
        )
        path_change_signalspy = QtTest.QSignalSpy(change_path_widget.pathSelected)

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("This is a new path")

        # Check signal is emitted
        self.assertTrue(
            path_change_signalspy.isValid(), "Path change signal is emitted"
        )
        self.assertEqual(
            len(path_change_signalspy), 1, "Path change signal is emitted once"
        )
        self.assertEqual(
            path_change_signalspy[0],
            ["This is a new path"],
            "Path change signal has the correct data",
        )

        # Changes are saved in DB
        divelog = self.database.storagelocation_get_by_id(6)
        self.assertEqual(
            divelog.path, "This is a new path", "Path is updated in database"
        )

        # New path is displayed
        path_wrapper_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        )
        path_widget = path_wrapper_layout.itemAt(0).widget()
        self.assertEqual(
            path_widget.text(), "This is a new path", "Path is updated on display"
        )

    def test_settings_method_display(self):
        method = self.database.conversionmethods_get_by_name("DarkTherapee")
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Check overall structure
        self.assertEqual(
            methodList.ui["layout"].columnCount(),
            7,
            "Conversion method display has the right number of colums",
        )
        self.assertEqual(
            methodList.ui["layout"].rowCount(),
            4,
            "Conversion method display has the right number of rows",
        )

        # Check name display
        name_wrapper = methodList.ui["layout"].itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()
        name_label = name_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEqual(
            name_label.text(), method.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = methodList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_name_button, IconButton),
            "Change name button is a IconButton",
        )

        # Check suffix display
        suffix_wrapper = methodList.ui["layout"].itemAtPosition(1, 2).widget()
        suffix_stack = suffix_wrapper.layout().itemAt(0).widget()
        suffix_label = suffix_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(suffix_label, QtWidgets.QLabel), "Suffix field is a QLabel"
        )
        self.assertEqual(
            suffix_label.text(),
            method.suffix,
            "Suffix field displays the expected data",
        )

        # Check "change suffix" display
        change_suffix_widget = methodList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertTrue(
            isinstance(change_suffix_widget, QtWidgets.QWidget),
            "Change suffix field is a QWidget",
        )
        change_suffix_button = change_suffix_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_suffix_button, IconButton),
            "Change suffix button is a IconButton",
        )

        # Check command display
        command_wrapper = methodList.ui["layout"].itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()
        command_label = command_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(command_label, QtWidgets.QLabel), "Command field is a QLabel"
        )
        self.assertEqual(
            command_label.text(),
            method.command,
            "Command field displays the expected data",
        )

        # Check "change command" display
        change_command_widget = methodList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertTrue(
            isinstance(change_command_widget, QtWidgets.QWidget),
            "Change command field is a QWidget",
        )
        change_command_button = change_command_widget.layout().currentWidget()
        self.assertTrue(
            isinstance(change_command_button, IconButton),
            "Change command button is a IconButton",
        )

        # Check Delete display
        delete_widget = methodList.ui["layout"].itemAtPosition(1, 6).widget()
        self.assertTrue(
            isinstance(delete_widget, IconButton),
            "Delete button is a IconButton",
        )

        # Check "Add new" display
        add_new_widget = methodList.ui["layout"].itemAtPosition(3, 1).widget()
        self.assertTrue(
            isinstance(add_new_widget, IconButton),
            "Add new button is a IconButton",
        )

    def test_settings_method_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get name-related widgets
        name_wrapper = methodList.ui["layout"].itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()
        name_label = name_stack.layout().currentWidget()

        name_change_layout = (
            methodList.ui["layout"].itemAtPosition(1, 1).widget().layout()
        )
        name_change_start = name_change_layout.currentWidget()

        # Check "name change start" receivers
        self.assertEqual(name_change_start.receivers(name_change_start.clicked), 1)
        name_change_start_signalspy = QtTest.QSignalSpy(name_change_start.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(name_change_start, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_start_signalspy.isValid(), "Name change start signal is emitted"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the dive log
        name_edit = name_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEqual(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the dive log's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEqual(
            name_change_start, name_change_end, "Edit button replaced by Save button"
        )

        # Check "name change end" receivers
        self.assertEqual(name_change_end.receivers(name_change_end.clicked), 1)
        name_change_end_signalspy = QtTest.QSignalSpy(name_change_end.clicked)

        # Change the name in UI & save changes
        name_edit.setText("DarkTherapee updated")
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            name_change_end_signalspy.isValid(), "Name change end signal is emitted"
        )
        self.assertEqual(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEqual(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_suffix("DT")
        self.assertEqual(
            method.name, "DarkTherapee updated", "Name is updated in database"
        )

        # Display is back to initial state
        name_widget = name_stack.layout().currentWidget()
        self.assertEqual(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEqual(
            name_label.text(), "DarkTherapee updated", "Name is updated on display"
        )

        name_change_widget = name_change_layout.currentWidget()
        self.assertEqual(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_method_edit_name_empty_error(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get name-related widgets
        name_wrapper = methodList.ui["layout"].itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()

        name_change_layout = (
            methodList.ui["layout"].itemAtPosition(1, 1).widget().layout()
        )
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        QtTest.QTest.mouseClick(name_change_start, Qt.LeftButton)
        name_edit = name_stack.layout().currentWidget()
        name_change_end = name_change_layout.currentWidget()

        # Change the name in UI & (try to) save changes
        name_edit.setText("")
        QtTest.QTest.mouseClick(name_change_end, Qt.LeftButton)

        # Error is displayed
        name_error = name_wrapper.layout().itemAt(1).widget()
        self.assertEqual(
            name_error.text(), "Missing conversion method name", "Error is displayed"
        )

        # Changes are not saved in DB
        method = self.database.conversionmethods_get()[1]
        self.assertNotEqual(method.name, "", "Name is not modified to empty")

    def test_settings_method_edit_suffix(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get suffix-related widgets
        suffix_wrapper = methodList.ui["layout"].itemAtPosition(1, 2).widget()
        suffix_stack = suffix_wrapper.layout().itemAt(0).widget()
        suffix_label = suffix_stack.layout().currentWidget()

        suffix_change_layout = (
            methodList.ui["layout"].itemAtPosition(1, 3).widget().layout()
        )
        suffix_change_start = suffix_change_layout.currentWidget()

        # Check "suffix change start" receivers
        self.assertEqual(suffix_change_start.receivers(suffix_change_start.clicked), 1)
        suffix_change_start_signalspy = QtTest.QSignalSpy(suffix_change_start.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(suffix_change_start, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            suffix_change_start_signalspy.isValid(),
            "Suffix change start signal is emitted",
        )
        self.assertEqual(
            len(suffix_change_start_signalspy),
            1,
            "Suffix change start signal is emitted once",
        )

        # Suffix is now editable & contains the suffix of the dive log
        suffix_edit = suffix_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(suffix_edit, QtWidgets.QLineEdit),
            "Suffix edit field now displayed",
        )
        self.assertEqual(
            suffix_edit.text(),
            suffix_label.text(),
            "Suffix edit field contains the dive log's suffix",
        )

        # Suffix edit button changed
        suffix_change_end = suffix_change_layout.currentWidget()
        self.assertNotEqual(
            suffix_change_start,
            suffix_change_end,
            "Edit button replaced by Save button",
        )

        # Check "suffix change end" receivers
        self.assertEqual(suffix_change_end.receivers(suffix_change_end.clicked), 1)
        suffix_change_end_signalspy = QtTest.QSignalSpy(suffix_change_end.clicked)

        # Change the suffix in UI & save changes
        suffix_edit.setText("DTU")
        QtTest.QTest.mouseClick(suffix_change_end, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            suffix_change_end_signalspy.isValid(), "Suffix change end signal is emitted"
        )
        self.assertEqual(
            len(suffix_change_end_signalspy),
            1,
            "Suffix change end signal is emitted once",
        )
        self.assertEqual(
            len(suffix_change_start_signalspy),
            1,
            "Suffix change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_name("DarkTherapee")
        self.assertEqual(method.suffix, "DTU", "Suffix is updated in database")

        # Display is back to initial state
        suffix_widget = suffix_stack.layout().currentWidget()
        self.assertEqual(
            suffix_widget, suffix_label, "Saving displays the suffix as QLabel"
        )
        self.assertEqual(suffix_label.text(), "DTU", "Suffix is updated on display")

        suffix_change_widget = suffix_change_layout.currentWidget()
        self.assertEqual(
            suffix_change_widget,
            suffix_change_start,
            "Save button replaced by Edit button",
        )

    def test_settings_method_edit_command(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get command-related widgets
        command_wrapper = methodList.ui["layout"].itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()
        command_label = command_stack.layout().currentWidget()

        command_change_layout = (
            methodList.ui["layout"].itemAtPosition(1, 5).widget().layout()
        )
        command_change_start = command_change_layout.currentWidget()

        # Check "command change start" receivers
        self.assertEqual(
            command_change_start.receivers(command_change_start.clicked), 1
        )
        command_change_start_signalspy = QtTest.QSignalSpy(command_change_start.clicked)

        # Display edit fields
        QtTest.QTest.mouseClick(command_change_start, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            command_change_start_signalspy.isValid(),
            "Command change start signal is emitted",
        )
        self.assertEqual(
            len(command_change_start_signalspy),
            1,
            "Command change start signal is emitted once",
        )

        # Command is now editable & contains the command of the dive log
        command_edit = command_stack.layout().currentWidget()
        self.assertTrue(
            isinstance(command_edit, QtWidgets.QLineEdit),
            "Command edit field now displayed",
        )
        self.assertEqual(
            command_edit.text(),
            command_label.text(),
            "Command edit field contains the dive log's command",
        )

        # Command edit button changed
        command_change_end = command_change_layout.currentWidget()
        self.assertNotEqual(
            command_change_start,
            command_change_end,
            "Edit button replaced by Save button",
        )

        # Check "command change end" receivers
        self.assertEqual(command_change_end.receivers(command_change_end.clicked), 1)
        command_change_end_signalspy = QtTest.QSignalSpy(command_change_end.clicked)

        # Change the command in UI & save changes
        command_edit.setText("../conversion.py -type DT")
        QtTest.QTest.mouseClick(command_change_end, Qt.LeftButton)

        # Check signal is emitted
        self.assertTrue(
            command_change_end_signalspy.isValid(),
            "Command change end signal is emitted",
        )
        self.assertEqual(
            len(command_change_end_signalspy),
            1,
            "Command change end signal is emitted once",
        )
        self.assertEqual(
            len(command_change_start_signalspy),
            1,
            "Command change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_name("DarkTherapee")
        self.assertEqual(
            method.command,
            "../conversion.py -type DT",
            "Command is updated in database",
        )

        # Display is back to initial state
        command_widget = command_stack.layout().currentWidget()
        self.assertEqual(
            command_widget, command_label, "Saving displays the command as QLabel"
        )
        self.assertEqual(
            command_label.text(),
            "../conversion.py -type DT",
            "Command is updated on display",
        )

        command_change_widget = command_change_layout.currentWidget()
        self.assertEqual(
            command_change_widget,
            command_change_start,
            "Save button replaced by Edit button",
        )

    def test_settings_method_edit_command_empty_error(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get command-related widgets
        command_wrapper = methodList.ui["layout"].itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()

        command_change_layout = (
            methodList.ui["layout"].itemAtPosition(1, 5).widget().layout()
        )
        command_change_start = command_change_layout.currentWidget()

        # Display edit fields
        QtTest.QTest.mouseClick(command_change_start, Qt.LeftButton)

        # Empty command field and validate
        command_edit = command_stack.layout().currentWidget()
        command_edit.setText("")
        command_change_end = command_change_layout.currentWidget()
        QtTest.QTest.mouseClick(command_change_end, Qt.LeftButton)
        # This checks part of the code where the same field has 2 errors in a row
        QtTest.QTest.mouseClick(command_change_end, Qt.LeftButton)

        # Error is displayed
        command_error = command_wrapper.layout().itemAt(1).widget()
        self.assertEqual(
            command_error.text(),
            "Missing conversion method command",
            "Error is displayed",
        )

        # Changes are not saved in DB
        method = self.database.conversionmethods_get()[1]
        self.assertNotEqual(method.command, "", "Command is not modified to empty")

    def test_settings_method_add_ok(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Click "Add new"
        add_new = methodList.ui["layout"].itemAtPosition(3, 1).widget()
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = methodList.ui["layout"].itemAtPosition(3, 0).widget()
        name_edit = name_wrapper.layout().itemAt(0).widget()
        suffix_wrapper = methodList.ui["layout"].itemAtPosition(3, 2).widget()
        suffix_edit = suffix_wrapper.layout().itemAt(0).widget()
        command_wrapper = methodList.ui["layout"].itemAtPosition(3, 4).widget()
        command_edit = command_wrapper.layout().itemAt(0).widget()

        # Input some data and save
        fields = {
            "name": "New method",
            "suffix": "NM",
            "command": "./new_method.py %TARGET_FILE%",
        }
        name_edit.setText(fields["name"])
        suffix_edit.setText(fields["suffix"])
        command_edit.setText(fields["command"])
        save_button = methodList.ui["layout"].itemAtPosition(3, 6).widget()
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        # Data is saved in DB
        method = self.database.conversionmethods_get_by_name(fields["name"])
        self.assertEqual(method.suffix, fields["suffix"], "Suffix is saved in DB")
        self.assertEqual(method.command, fields["command"], "Command is saved in DB")

        # Check display of the new command
        self.assertEqual(methodList.ui["layout"].rowCount(), 5, "Row count is correct")
        for column, field in enumerate(fields.keys()):
            wrapper = methodList.ui["layout"].itemAtPosition(3, column * 2).widget()
            stack = wrapper.layout().itemAt(0).widget()
            label = stack.layout().currentWidget()
            self.assertEqual(label.text(), fields[field], "Data is displayed properly")

    def test_settings_method_add_with_errors(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Click "Add new"
        add_new = methodList.ui["layout"].itemAtPosition(3, 1).widget()
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = methodList.ui["layout"].itemAtPosition(3, 0).widget()
        name_edit = name_wrapper.layout().itemAt(0).widget()
        command_wrapper = methodList.ui["layout"].itemAtPosition(3, 4).widget()
        command_edit = command_wrapper.layout().itemAt(0).widget()

        # Save with blank fields & check errors
        save_button = methodList.ui["layout"].itemAtPosition(3, 6).widget()
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNotNone(name_wrapper.layout().itemAt(1), "Name error is displayed")
        name_error = name_wrapper.layout().itemAt(1).widget()
        self.assertEqual(
            name_error.text(),
            "Missing conversion method name",
            "Name error displays correct error",
        )

        self.assertIsNotNone(
            command_wrapper.layout().itemAt(1), "Command error is displayed"
        )
        command_error = command_wrapper.layout().itemAt(1).widget()
        self.assertEqual(
            command_error.text(),
            "Missing conversion method command",
            "Command error displays correct error",
        )

        # Click "Add new", all errors should be hidden
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)
        name_wrapper = methodList.ui["layout"].itemAtPosition(3, 0).widget()
        name_layout = name_wrapper.layout()
        name_edit = name_layout.itemAt(0).widget()
        command_wrapper = methodList.ui["layout"].itemAtPosition(3, 4).widget()
        command_layout = command_wrapper.layout()
        command_edit = command_layout.itemAt(0).widget()

        self.assertIsNone(name_layout.itemAt(1), "Name error is hidden")
        self.assertIsNone(command_layout.itemAt(1), "Command error is hidden")

        # Enter name, check error is hidden now
        name_edit.setText("New method")
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNone(name_layout.itemAt(1), "Name error is hidden")
        self.assertIsNotNone(command_layout.itemAt(1), "Command error is displayed")

        # Enter command, empty name, check error is hidden now
        name_edit.setText("")
        command_edit.setText("../command_to_convert")
        QtTest.QTest.mouseClick(save_button, Qt.LeftButton)

        self.assertIsNotNone(name_layout.itemAt(1), "Name error is displayed")
        self.assertIsNone(command_layout.itemAt(1), "Command error is hidden")

    def test_settings_method_add_new_twice(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Click "Add new" twice
        add_new = methodList.ui["layout"].itemAtPosition(3, 1).widget()
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)
        QtTest.QTest.mouseClick(add_new, Qt.LeftButton)

        # "New location" fields are visible only once
        self.assertEqual(methodList.ui["layout"].rowCount(), 5, "Only 1 line is added")


if __name__ == "__main__":
    unittest.main()
