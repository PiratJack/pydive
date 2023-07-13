import os
import sys
import unittest
import datetime
import logging
from PyQt5 import QtWidgets, QtTest, QtCore
from PyQt5.QtCore import Qt

sys.path.append("pydive")

import pydive.models.database as databasemodel
import pydive
import pydive.controllers as controllers
import pydive.controllers.mainwindow
import pydive.controllers.widgets.iconbutton
import pydive.controllers.widgets.pathselectbutton

from pydive.models.storagelocation import StorageLocation
from pydive.models.storagelocation import StorageLocationType
from pydive.models.conversionmethod import ConversionMethod

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"
BASE_FOLDER = "./test_images" + str(int(datetime.datetime.now().timestamp())) + "/"

app = QtWidgets.QApplication(sys.argv)


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

        self.mainwindow = pydive.controllers.mainwindow.MainWindow(self.database)

    def tearDown(self):
        self.mainwindow.close()
        self.mainwindow.database.session.close()
        self.mainwindow.database.engine.dispose()
        # Delete database
        os.remove(DATABASE_FILE)

        # Delete folders
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
            6,
            "Locations have the right number of rows",
        )

        # Check name display
        name_layout = locationList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEquals(
            name_label.text(), location.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = locationList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_name_button, pydive.controllers.widgets.iconbutton.IconButton), "Change name button is a IconButton")

        # Check path display
        path_widget = locationList.ui["layout"].itemAtPosition(1, 2).widget()
        self.assertTrue(
            isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEquals(
            path_widget.text(), location.path, "Path field displays the expected data"
        )

        # Check "change path" display
        change_path_widget = locationList.ui["layout"].itemAtPosition(1, 3).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_path_widget, pydive.controllers.widgets.pathselectbutton.PathSelectButton), "Change path button is a PathSelectButton")

        # Check Delete display
        delete_widget = locationList.ui["layout"].itemAtPosition(1, 4).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(delete_widget, pydive.controllers.widgets.iconbutton.IconButton), "Delete button is a IconButton")

        # Check "Add new" display
        add_new_widget = locationList.ui["layout"].itemAtPosition(5, 1).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(add_new_widget, pydive.controllers.widgets.iconbutton.IconButton), "Add new button is a IconButton")

    def test_settings_location_list_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get name-related widgets
        name_layout = locationList.ui["layout"].itemAtPosition(1, 0).widget().layout()
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
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the storage location
        name_edit = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEquals(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the location's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEquals(
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
        self.assertEquals(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        location = self.database.storagelocation_get_by_id(1)
        self.assertEquals(location.name, "SD Card", "Name is updated in database")

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        self.assertEquals(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEquals(name_label.text(), "SD Card", "Name is updated on display")

        name_change_widget = name_change_layout.currentWidget()
        self.assertEquals(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_location_list_edit_path(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get change path button
        change_path_widget = locationList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertEquals(change_path_widget.target_type, "folder")

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
        self.assertEquals(
            len(path_change_signalspy), 1, "Path change signal is emitted once"
        )
        self.assertEquals(
            path_change_signalspy[0],
            ["This is a new path"],
            "Path change signal has the correct data",
        )

        # Changes are saved in DB
        location = self.database.storagelocation_get_by_id(1)
        self.assertEquals(
            location.path,
            os.path.join("This is a new path", ""),
            "Path is updated in database",
        )

        # New path is displayed
        path_widget = locationList.ui["layout"].itemAtPosition(1, 2).widget()
        self.assertEquals(
            path_widget.text(), "This is a new path", "Path is updated on display"
        )

    @unittest.skip("TODO Does not work, triggers with same callback twice")
    def test_settings_location_list_delete_cancel(self):
        settingsController = self.mainwindow.controllers["Settings"]
        locationList = settingsController.locations_list

        # Get delete button
        delete_widget = locationList.ui["layout"].itemAtPosition(1, 4).widget()

        # Check there is no change in DB
        def check_location_exists():
            messagebox = app.activeModalWidget()
            QtTest.QTest.mouseClick(
                messagebox.button(QtWidgets.QMessageBox.No), Qt.LeftButton
            )

            location = self.database.storagelocation_get_by_id(1)
            self.assertEquals(location.name, "Camera", "Location still exists")
            print("test_exists")

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
            messagebox = app.activeModalWidget()
            QtTest.QTest.mouseClick(
                messagebox.button(QtWidgets.QMessageBox.Yes), Qt.LeftButton
            )

            # Check the DB has been updated
            location = self.database.storagelocation_get_by_id(2)
            self.assertEquals(location, None, "Location has been deleted")

            # Location no longer visible in UI
            self.assertEquals(
                locationList.ui["layout"].rowCount(),
                5,
                "Locations have the right number of rows",
            )
            self.assertEquals(
                locationList.ui["layout"].rowCount(),
                5,
                "Locations have the right number of rows",
            )
            print("test_delete")

        # Click delete, then "Yes" in the dialog
        timer2 = QtCore.QTimer(settingsController.ui["main"])
        timer2.timeout.connect(check_location_deleted)
        timer2.start(300)
        QtTest.QTest.mouseClick(delete_widget, Qt.LeftButton)

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
        name_layout = divelogList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEquals(
            name_label.text(), divelog.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = divelogList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_name_button, pydive.controllers.widgets.iconbutton.IconButton), "Change name button is a IconButton")

        # Check path display
        path_widget = divelogList.ui["layout"].itemAtPosition(1, 2).widget()
        self.assertTrue(
            isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        )
        self.assertEquals(
            path_widget.text(), divelog.path, "Path field displays the expected data"
        )

        # Check "change path" display
        change_path_widget = divelogList.ui["layout"].itemAtPosition(1, 3).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_path_widget, pydive.controllers.widgets.pathselectbutton.PathSelectButton), "Change path button is a PathSelectButton")

        # Check Delete display
        delete_widget = divelogList.ui["layout"].itemAtPosition(1, 4)
        self.assertEquals(delete_widget, None, "Impossible to delete divelog file")

    def test_settings_divelog_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        divelogList = settingsController.divelog_list

        # Get name-related widgets
        name_layout = divelogList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = (
            divelogList.ui["layout"].itemAtPosition(1, 1).widget().layout()
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
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the dive log
        name_edit = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEquals(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the dive log's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEquals(
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
        self.assertEquals(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        divelog = self.database.storagelocation_get_by_id(6)
        self.assertEquals(
            divelog.name, "Subsurface file", "Name is updated in database"
        )

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        self.assertEquals(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEquals(
            name_label.text(), "Subsurface file", "Name is updated on display"
        )

        name_change_widget = name_change_layout.currentWidget()
        self.assertEquals(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_divelog_edit_path(self):
        settingsController = self.mainwindow.controllers["Settings"]
        divelogList = settingsController.divelog_list

        # Get change path button
        change_path_widget = divelogList.ui["layout"].itemAtPosition(1, 3).widget()
        self.assertEquals(change_path_widget.target_type, "file")

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
        self.assertEquals(
            len(path_change_signalspy), 1, "Path change signal is emitted once"
        )
        self.assertEquals(
            path_change_signalspy[0],
            ["This is a new path"],
            "Path change signal has the correct data",
        )

        # Changes are saved in DB
        divelog = self.database.storagelocation_get_by_id(6)
        self.assertEquals(
            divelog.path, "This is a new path", "Path is updated in database"
        )

        # New path is displayed
        path_widget = divelogList.ui["layout"].itemAtPosition(1, 2).widget()
        self.assertEquals(
            path_widget.text(), "This is a new path", "Path is updated on display"
        )

    def test_settings_conversion_method_display(self):
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
        name_layout = methodList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        name_label = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        )
        self.assertEquals(
            name_label.text(), method.name, "Name field displays the expected data"
        )

        # Check "change name" display
        change_name_widget = methodList.ui["layout"].itemAtPosition(1, 1).widget()
        self.assertTrue(
            isinstance(change_name_widget, QtWidgets.QWidget),
            "Change name field is a QWidget",
        )
        change_name_button = change_name_widget.layout().currentWidget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_name_button, pydive.controllers.widgets.iconbutton.IconButton), "Change name button is a IconButton")

        # Check suffix display
        suffix_layout = methodList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        suffix_label = suffix_layout.currentWidget()
        self.assertTrue(
            isinstance(suffix_label, QtWidgets.QLabel), "Suffix field is a QLabel"
        )
        self.assertEquals(
            suffix_label.text(),
            method.suffix,
            "Suffix field displays the expected data",
        )

        # Check "change suffix" display
        change_suffix_widget = methodList.ui["layout"].itemAtPosition(1, 3).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_suffix_widget, pydive.controllers.widgets.iconbutton.IconButton), "Change suffix button is a IconButton")

        # Check command display
        command_layout = methodList.ui["layout"].itemAtPosition(1, 4).widget().layout()
        command_label = command_layout.currentWidget()
        self.assertTrue(
            isinstance(command_label, QtWidgets.QLabel), "Command field is a QLabel"
        )
        self.assertEquals(
            command_label.text(),
            method.command,
            "Command field displays the expected data",
        )

        # Check "change command" display
        change_command_widget = methodList.ui["layout"].itemAtPosition(1, 5).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(change_command_widget, pydive.controllers.widgets.iconbutton.IconButton), "Change command button is a IconButton")

        # Check Delete display
        delete_widget = methodList.ui["layout"].itemAtPosition(1, 6).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(delete_widget, pydive.controllers.widgets.iconbutton.IconButton), "Delete button is a IconButton")

        # Check "Add new" display
        add_new_widget = methodList.ui["layout"].itemAtPosition(3, 1).widget()
        # TODO The below assertion should be True, but it's not...
        # self.assertTrue(isinstance(add_new_widget, pydive.controllers.widgets.iconbutton.IconButton), "Add new button is a IconButton")

    def test_settings_method_edit_name(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get name-related widgets
        name_layout = methodList.ui["layout"].itemAtPosition(1, 0).widget().layout()
        name_label = name_layout.currentWidget()

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
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is emitted once",
        )

        # Name is now editable & contains the name of the dive log
        name_edit = name_layout.currentWidget()
        self.assertTrue(
            isinstance(name_edit, QtWidgets.QLineEdit), "Name edit field now displayed"
        )
        self.assertEquals(
            name_edit.text(),
            name_label.text(),
            "Name edit field contains the dive log's name",
        )

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        self.assertNotEquals(
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
        self.assertEquals(
            len(name_change_end_signalspy), 1, "Name change end signal is emitted once"
        )
        self.assertEquals(
            len(name_change_start_signalspy),
            1,
            "Name change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_suffix("DT")
        self.assertEquals(
            method.name, "DarkTherapee updated", "Name is updated in database"
        )

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        self.assertEquals(name_widget, name_label, "Saving displays the name as QLabel")
        self.assertEquals(
            name_label.text(), "DarkTherapee updated", "Name is updated on display"
        )

        name_change_widget = name_change_layout.currentWidget()
        self.assertEquals(
            name_change_widget, name_change_start, "Save button replaced by Edit button"
        )

    def test_settings_method_edit_suffix(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get suffix-related widgets
        suffix_layout = methodList.ui["layout"].itemAtPosition(1, 2).widget().layout()
        suffix_label = suffix_layout.currentWidget()

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
        self.assertEquals(
            len(suffix_change_start_signalspy),
            1,
            "Suffix change start signal is emitted once",
        )

        # Suffix is now editable & contains the suffix of the dive log
        suffix_edit = suffix_layout.currentWidget()
        self.assertTrue(
            isinstance(suffix_edit, QtWidgets.QLineEdit),
            "Suffix edit field now displayed",
        )
        self.assertEquals(
            suffix_edit.text(),
            suffix_label.text(),
            "Suffix edit field contains the dive log's suffix",
        )

        # Suffix edit button changed
        suffix_change_end = suffix_change_layout.currentWidget()
        self.assertNotEquals(
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
        self.assertEquals(
            len(suffix_change_end_signalspy),
            1,
            "Suffix change end signal is emitted once",
        )
        self.assertEquals(
            len(suffix_change_start_signalspy),
            1,
            "Suffix change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_name("DarkTherapee")
        self.assertEquals(method.suffix, "DTU", "Suffix is updated in database")

        # Display is back to initial state
        suffix_widget = suffix_layout.currentWidget()
        self.assertEquals(
            suffix_widget, suffix_label, "Saving displays the suffix as QLabel"
        )
        self.assertEquals(suffix_label.text(), "DTU", "Suffix is updated on display")

        suffix_change_widget = suffix_change_layout.currentWidget()
        self.assertEquals(
            suffix_change_widget,
            suffix_change_start,
            "Save button replaced by Edit button",
        )

    def test_settings_method_edit_command(self):
        settingsController = self.mainwindow.controllers["Settings"]
        methodList = settingsController.conversion_methods_list

        # Get command-related widgets
        command_layout = methodList.ui["layout"].itemAtPosition(1, 4).widget().layout()
        command_label = command_layout.currentWidget()

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
        self.assertEquals(
            len(command_change_start_signalspy),
            1,
            "Command change start signal is emitted once",
        )

        # Command is now editable & contains the command of the dive log
        command_edit = command_layout.currentWidget()
        self.assertTrue(
            isinstance(command_edit, QtWidgets.QLineEdit),
            "Command edit field now displayed",
        )
        self.assertEquals(
            command_edit.text(),
            command_label.text(),
            "Command edit field contains the dive log's command",
        )

        # Command edit button changed
        command_change_end = command_change_layout.currentWidget()
        self.assertNotEquals(
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
        self.assertEquals(
            len(command_change_end_signalspy),
            1,
            "Command change end signal is emitted once",
        )
        self.assertEquals(
            len(command_change_start_signalspy),
            1,
            "Command change start signal is not emitted a second time",
        )

        # Changes are saved in DB
        method = self.database.conversionmethods_get_by_name("DarkTherapee")
        self.assertEquals(
            method.command,
            "../conversion.py -type DT",
            "Command is updated in database",
        )

        # Display is back to initial state
        command_widget = command_layout.currentWidget()
        self.assertEquals(
            command_widget, command_label, "Saving displays the command as QLabel"
        )
        self.assertEquals(
            command_label.text(),
            "../conversion.py -type DT",
            "Command is updated on display",
        )

        command_change_widget = command_change_layout.currentWidget()
        self.assertEquals(
            command_change_widget,
            command_change_start,
            "Save button replaced by Edit button",
        )