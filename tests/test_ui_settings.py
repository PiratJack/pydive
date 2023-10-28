import os
import sys
import pytest
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.iconbutton import IconButton

import sqlalchemy.orm.exc


class TestUiSettings:
    @pytest.fixture
    def pydive_settings(self, qtbot, pydive_mainwindow, pydive_fake_pictures):
        pydive_mainwindow.display_tab("Settings")
        self.all_files = pydive_fake_pictures

        yield pydive_mainwindow.layout.currentWidget()

    def test_settings_display(self, pydive_settings, pydive_db):
        # Check overall structure
        assert (
            pydive_settings.layout().count() == 11  # 2 per group + 3 stretchers
        ), "The overall screen has the right number of items"

    def test_settings_location_list_display(self, pydive_settings, pydive_db):
        location = pydive_db.storagelocation_get_by_id(1)
        locationListTitle = pydive_settings.layout().itemAt(0).widget()
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Check overall structure
        assert (
            locationListTitle.text() == "Image folders"
        ), "Image folders title display"
        assert (
            locationListLayout.columnCount() == 5
        ), "Locations have the right number of colums"
        assert (
            locationListLayout.rowCount() == 7
        ), "Locations have the right number of rows"

        # Check name display
        name_wrapper_layout = locationListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == location.name
        ), "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = locationListLayout.itemAtPosition(1, 1).widget()
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check path display
        path_wrapper_layout = locationListLayout.itemAtPosition(1, 2).widget().layout()
        path_widget = path_wrapper_layout.itemAt(0).widget()
        assert isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_widget.text() == location.path
        ), "Path field displays the expected data"

        # Check "change path" display
        change_path_widget = locationListLayout.itemAtPosition(1, 3).widget()
        assert isinstance(
            change_path_widget, PathSelectButton
        ), "Change path button is a PathSelectButton"

        # Check Delete display
        delete_widget = locationListLayout.itemAtPosition(1, 4).widget()
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

        # Check "Add new" display
        add_new_widget = locationListLayout.itemAtPosition(6, 1).widget()
        assert isinstance(add_new_widget, IconButton), "Add new button is a IconButton"

    def test_settings_location_list_edit_name(self, pydive_settings, pydive_db, qtbot):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get name-related widgets
        name_wrapper_layout = locationListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = locationListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        with qtbot.waitSignal(name_change_start.clicked, timeout=1000):
            qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Name is now editable & contains the name of the storage location
        name_edit = name_layout.currentWidget()
        assert isinstance(
            name_edit, QtWidgets.QLineEdit
        ), "Name edit field now displayed"
        assert (
            name_edit.text() == name_label.text()
        ), "Name edit field contains the location's name"

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        assert (
            name_change_start != name_change_end
        ), "Edit button replaced by Save button"

        # Change the name in UI & save changes
        name_edit.setText("SD Card")
        with qtbot.waitSignal(name_change_end.clicked, timeout=1000):
            qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Changes are saved in DB
        location = pydive_db.storagelocation_get_by_id(1)
        assert location.name == "SD Card", "Name is updated in database"

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        assert name_widget == name_label, "Saving displays the name as QLabel"
        assert name_label.text() == "SD Card", "Name is updated on display"

        name_change_widget = name_change_layout.currentWidget()
        assert (
            name_change_widget == name_change_start
        ), "Save button replaced by Edit button"

    def test_settings_location_list_edit_name_error(
        self, pydive_settings, pydive_db, qtbot
    ):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get name-related widgets
        name_wrapper_layout = locationListLayout.itemAtPosition(1, 0).widget().layout()
        name_change_layout = locationListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Change the name
        name_edit = name_wrapper_layout.itemAt(0).widget().layout().currentWidget()
        name_edit.setText("")

        # Save changes
        name_change_end = name_change_layout.currentWidget()
        qtbot.mouseClick(name_change_end, Qt.LeftButton)
        # Triggered twice to test when errors were displayed before
        qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Check error is displayed
        error_widget = name_wrapper_layout.itemAt(1).widget()
        assert (
            error_widget.text() == "Missing storage location name"
        ), "Error gets displayed"

        # Changes are not saved in DB
        location = pydive_db.storagelocation_get_by_id(1)
        assert location.name != "", "Name is not modified to empty"

    def test_settings_location_list_edit_path(self, pydive_settings, pydive_db):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get change path button
        change_path_widget = locationListLayout.itemAtPosition(1, 3).widget()
        assert (
            change_path_widget.target_type == "folder"
        ), "Path change looks for folders"

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("This is a new path")

        # Changes are saved in DB
        location = pydive_db.storagelocation_get_by_id(1)
        assert location.path == os.path.join(
            "This is a new path", ""
        ), "Path is updated in database"

        # New path is displayed
        path_wrapper_layout = locationListLayout.itemAtPosition(1, 2).widget().layout()
        path_widget = path_wrapper_layout.itemAt(0).widget()
        assert path_widget.text() == "This is a new path", "Path is updated on display"

    def test_settings_location_list_edit_path_error(self, pydive_settings):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get change path button
        change_path_widget = locationListLayout.itemAtPosition(1, 3).widget()

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("")

        # Error message is displayed
        path_wrapper_layout = locationListLayout.itemAtPosition(1, 2).widget().layout()
        error_widget = path_wrapper_layout.itemAt(1).widget()
        assert (
            error_widget.text() == "Missing storage location path"
        ), "Error gets displayed"

    def test_settings_location_list_delete_cancel(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get delete button
        delete_widget = locationListLayout.itemAtPosition(1, 4).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.No
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        location = pydive_db.storagelocation_get_by_id(1)
        assert location.name == "Camera", "Location still exists"

    def test_settings_location_list_delete_confirm(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get delete button
        delete_widget = locationListLayout.itemAtPosition(2, 4).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            pydive_db.storagelocation_get_by_id(2)

        # Location no longer visible in UI
        name = locationListLayout.itemAtPosition(2, 0)
        assert name is None, "Location is deleted from UI"

    def test_settings_location_list_add_location_display(self, pydive_settings, qtbot):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get "add new" button
        add_new = locationListLayout.itemAtPosition(6, 1).widget()

        # Display edit fields
        with qtbot.waitSignal(add_new.clicked, timeout=1000):
            qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are now displayed
        name_wrapper = locationListLayout.itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        assert isinstance(
            name_label, QtWidgets.QLineEdit
        ), "Add new - name is a QLineEdit"
        assert name_label.text() == "", "Add new - name field is empty"

        path_wrapper = locationListLayout.itemAtPosition(6, 2).widget().layout()
        path_label = path_wrapper.itemAt(0).widget()
        assert isinstance(
            path_label, QtWidgets.QLineEdit
        ), "Add new - path is a QLineEdit"
        assert path_label.text() == "", "Add new - path field is empty"

        path_change = locationListLayout.itemAtPosition(6, 3).widget()
        assert isinstance(
            path_change, IconButton
        ), "Add new - path change is an IconButton"

    def test_settings_location_list_add_location_save(
        self, pydive_settings, pydive_db, qtbot
    ):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get "add new" button
        add_new = locationListLayout.itemAtPosition(6, 1).widget()

        # Display edit fields
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # Enter a new name
        name_wrapper = locationListLayout.itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()

        name_label.setText("New location")

        # Enter a new path
        path_change = locationListLayout.itemAtPosition(6, 3).widget()
        assert path_change.target_type == "folder", "Path change looks for folders"
        # Simulating the actual dialog is impossible (it's OS-provided)
        path_change.pathSelected.emit("New path")

        # Save changes
        save_button = locationListLayout.itemAtPosition(6, 4).widget()
        assert isinstance(save_button, IconButton), "Save button is an IconButton"
        qtbot.mouseClick(save_button, Qt.LeftButton)

        # Data is saved in DB
        location = pydive_db.storagelocation_get_by_name("New location")
        assert location.name == "New location", "Name is saved in database"
        assert location.path == "New path" + os.path.sep, "Path is saved in database"
        assert (
            location.type.value["name"] == "picture_folder"
        ), "Location type is saved in database"

        # Display is now similar as other locations
        assert locationListLayout.rowCount() == 8, "New line is added"

        # Check name display
        name_wrapper_layout = locationListLayout.itemAtPosition(6, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == location.name
        ), "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = locationListLayout.itemAtPosition(6, 1).widget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check path display
        path_wrapper_layout = locationListLayout.itemAtPosition(6, 2).widget().layout()
        path_widget = path_wrapper_layout.itemAt(0).widget()
        assert isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_widget.text() == location.path
        ), "Path field displays the expected data"

        # Check "change path" display
        change_path_widget = locationListLayout.itemAtPosition(6, 3).widget()
        assert isinstance(
            change_path_widget, PathSelectButton
        ), "Change path button is a PathSelectButton"

        # Check Delete display
        delete_widget = locationListLayout.itemAtPosition(6, 4).widget()
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

    def test_settings_location_list_add_new_twice(self, pydive_settings, qtbot):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Get "add new" button
        add_new = locationListLayout.itemAtPosition(6, 1).widget()

        # Display edit fields
        qtbot.mouseClick(add_new, Qt.LeftButton)
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # "New location" fields are visible only once
        assert locationListLayout.rowCount() == 8, "Only 1 line is added"

    def test_settings_location_list_add_with_errors(self, pydive_settings, qtbot):
        locationListLayout = pydive_settings.layout().itemAt(1).widget().layout()

        # Click "Add new"
        add_new = locationListLayout.itemAtPosition(6, 1).widget()
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = locationListLayout.itemAtPosition(6, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        path_wrapper = locationListLayout.itemAtPosition(6, 2).widget().layout()
        path_change = locationListLayout.itemAtPosition(6, 3).widget()
        save_button = locationListLayout.itemAtPosition(6, 4).widget()

        # Save with blank fields & check errors
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is not None, "Name error is displayed"
        name_error = name_wrapper.itemAt(1).widget()
        assert (
            name_error.text() == "Missing storage location name"
        ), "Name error displays correct error"

        assert path_wrapper.itemAt(1) is not None, "Path error is displayed"
        path_error = path_wrapper.itemAt(1).widget()
        assert (
            path_error.text() == "Missing storage location path"
        ), "Path error displays correct error"

        # Click "Add new", all errors should be hidden
        qtbot.mouseClick(add_new, Qt.LeftButton)
        name_wrapper = locationListLayout.itemAtPosition(6, 0).widget().layout()
        path_wrapper = locationListLayout.itemAtPosition(6, 2).widget().layout()
        path_change = locationListLayout.itemAtPosition(6, 3).widget()
        save_button = locationListLayout.itemAtPosition(6, 4).widget()

        assert name_wrapper.itemAt(1) is None, "Name error is hidden"
        assert path_wrapper.itemAt(1) is None, "Path error is hidden"

        # Enter name, check error is hidden now
        name_label = name_wrapper.itemAt(0).widget()
        name_label.setText("New location")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is None, "Name error is hidden"
        assert path_wrapper.itemAt(1) is not None, "Path error is displayed"
        path_error = path_wrapper.itemAt(1).widget()
        assert (
            path_error.text() == "Missing storage location path"
        ), "Path error displays correct error"

        # Enter path, empty name, check error is hidden now
        path_change.pathSelected.emit("New path")
        name_label.setText("")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is not None, "Name error is displayed"
        name_error = name_wrapper.itemAt(1).widget()
        assert (
            name_error.text() == "Missing storage location name"
        ), "Name error displays correct error"

        assert path_wrapper.itemAt(1) is None, "Path error is hidden"

    def test_settings_divelog_display(self, pydive_settings, pydive_db):
        divelog = pydive_db.storagelocation_get_by_id(6)
        divelogListTitle = pydive_settings.layout().itemAt(3).widget()
        divelogListLayout = pydive_settings.layout().itemAt(4).widget().layout()

        # Check overall structure
        assert divelogListTitle.text() == "Dive log file", "Dive log file title display"
        assert (
            divelogListLayout.columnCount() == 5
        ), "Dive log display has the right number of colums"
        assert (
            divelogListLayout.rowCount() == 2
        ), "Dive log display has the right number of rows"

        # Check name display
        name_wrapper_layout = divelogListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == divelog.name
        ), "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = divelogListLayout.itemAtPosition(1, 1).widget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check path display
        path_wrapper_layout = divelogListLayout.itemAtPosition(1, 2).widget().layout()
        path_widget = path_wrapper_layout.itemAt(0).widget()
        assert isinstance(path_widget, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_widget.text() == divelog.path
        ), "Path field displays the expected data"

        # Check "change path" display
        change_path_widget = divelogListLayout.itemAtPosition(1, 3).widget()
        assert isinstance(
            change_path_widget, PathSelectButton
        ), "Change path button is a PathSelectButton"

        # Check Delete display
        delete_widget = divelogListLayout.itemAtPosition(1, 4)
        assert delete_widget == None, "Impossible to delete divelog file"

    def test_settings_divelog_edit_name(self, pydive_settings, pydive_db, qtbot):
        divelogListLayout = pydive_settings.layout().itemAt(4).widget().layout()

        # Get name-related widgets
        name_wrapper_layout = divelogListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = divelogListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()
        assert isinstance(
            name_change_start, IconButton
        ), "Name change button is a IconButton"

        # Display edit fields
        with qtbot.waitSignal(name_change_start.clicked, timeout=1000):
            qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Name is now editable & contains the name of the dive log
        name_edit = name_layout.currentWidget()
        assert isinstance(
            name_edit, QtWidgets.QLineEdit
        ), "Name edit field now displayed"
        assert (
            name_edit.text() == name_label.text()
        ), "Name edit field contains the dive log's name"

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        assert (
            name_change_start != name_change_end
        ), "Edit button replaced by Save button"

        # Change the name in UI & save changes
        name_edit.setText("Subsurface file")
        with qtbot.waitSignal(name_change_end.clicked, timeout=1000):
            qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Changes are saved in DB
        divelog = pydive_db.storagelocation_get_by_id(6)
        assert divelog.name == "Subsurface file", "Name is updated in database"

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        assert name_widget == name_label, "Saving displays the name as QLabel"
        assert name_label.text() == "Subsurface file", "Name is updated on display"

        name_change_widget = name_change_layout.currentWidget()
        assert (
            name_change_widget == name_change_start
        ), "Save button replaced by Edit button"

    def test_settings_divelog_edit_path(self, pydive_settings, pydive_db):
        divelogListLayout = pydive_settings.layout().itemAt(4).widget().layout()

        # Get change path button
        change_path_widget = divelogListLayout.itemAtPosition(1, 3).widget()
        assert change_path_widget.target_type == "file"

        # Simulating the actual dialog is impossible (it's OS-provided)
        change_path_widget.pathSelected.emit("This is a new path")

        # Changes are saved in DB
        divelog = pydive_db.storagelocation_get_by_id(6)
        assert divelog.path == "This is a new path", "Path is updated in database"

        # New path is displayed
        path_wrapper_layout = divelogListLayout.itemAtPosition(1, 2).widget().layout()
        path_widget = path_wrapper_layout.itemAt(0).widget()
        assert path_widget.text() == "This is a new path", "Path is updated on display"

    def test_settings_method_display(self, pydive_settings, pydive_db):
        method = pydive_db.conversionmethods_get_by_name("DarkTherapee")
        methodListTitle = pydive_settings.layout().itemAt(6).widget()
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Check overall structure
        assert (
            methodListTitle.text() == "Conversion methods"
        ), "Conversion methods title display"
        assert (
            methodListLayout.columnCount() == 7
        ), "Conversion method display has the right number of colums"
        assert (
            methodListLayout.rowCount() == 4
        ), "Conversion method display has the right number of rows"

        # Check name display
        name_wrapper = methodListLayout.itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()
        name_label = name_stack.layout().currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert name_label.text() == method.name, "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = methodListLayout.itemAtPosition(1, 1).widget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check suffix display
        suffix_wrapper = methodListLayout.itemAtPosition(1, 2).widget()
        suffix_stack = suffix_wrapper.layout().itemAt(0).widget()
        suffix_label = suffix_stack.layout().currentWidget()
        assert isinstance(suffix_label, QtWidgets.QLabel), "Suffix field is a QLabel"
        assert (
            suffix_label.text() == method.suffix
        ), "Suffix field displays the expected data"

        # Check "change suffix" display
        change_suffix_widget = methodListLayout.itemAtPosition(1, 3).widget()
        assert isinstance(
            change_suffix_widget, QtWidgets.QWidget
        ), "Change suffix field is a QWidget"
        change_suffix_button = change_suffix_widget.layout().currentWidget()
        assert isinstance(
            change_suffix_button, IconButton
        ), "Change suffix button is a IconButton"

        # Check command display
        command_wrapper = methodListLayout.itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()
        command_label = command_stack.layout().currentWidget()
        assert isinstance(command_label, QtWidgets.QLabel), "Command field is a QLabel"
        assert (
            command_label.text() == method.command
        ), "Command field displays the expected data"

        # Check "change command" display
        change_command_widget = methodListLayout.itemAtPosition(1, 3).widget()
        assert isinstance(
            change_command_widget, QtWidgets.QWidget
        ), "Change command field is a QWidget"
        change_command_button = change_command_widget.layout().currentWidget()
        assert isinstance(
            change_command_button, IconButton
        ), "Change command button is a IconButton"

        # Check Delete display
        delete_widget = methodListLayout.itemAtPosition(1, 6).widget()
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

        # Check "Add new" display
        add_new_widget = methodListLayout.itemAtPosition(3, 1).widget()
        assert isinstance(add_new_widget, IconButton), "Add new button is a IconButton"

    def test_settings_method_edit_name(self, pydive_settings, pydive_db, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get name-related widgets
        name_wrapper = methodListLayout.itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()
        name_label = name_stack.layout().currentWidget()

        name_change_layout = methodListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        with qtbot.waitSignal(name_change_start.clicked, timeout=1000):
            qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Name is now editable & contains the name of the dive log
        name_edit = name_stack.layout().currentWidget()
        assert isinstance(
            name_edit, QtWidgets.QLineEdit
        ), "Name edit field now displayed"
        assert (
            name_edit.text() == name_label.text()
        ), "Name edit field contains the dive log's name"

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        assert (
            name_change_start != name_change_end
        ), "Edit button replaced by Save button"

        # Change the name in UI & save changes
        name_edit.setText("DarkTherapee updated")
        with qtbot.waitSignal(name_change_end.clicked, timeout=1000):
            qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Changes are saved in DB
        method = pydive_db.conversionmethods_get_by_suffix("DT")
        assert method.name == "DarkTherapee updated", "Name is updated in database"

        # Display is back to initial state
        name_widget = name_stack.layout().currentWidget()
        assert name_widget == name_label, "Saving displays the name as QLabel"
        assert name_label.text() == "DarkTherapee updated", "Name is updated on display"

        name_change_widget = name_change_layout.currentWidget()
        assert (
            name_change_widget == name_change_start
        ), "Save button replaced by Edit button"

    def test_settings_method_edit_name_empty_error(
        self, pydive_settings, pydive_db, qtbot
    ):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get name-related widgets
        name_wrapper = methodListLayout.itemAtPosition(1, 0).widget()
        name_stack = name_wrapper.layout().itemAt(0).widget()

        name_change_layout = methodListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(name_change_start, Qt.LeftButton)
        name_edit = name_stack.layout().currentWidget()
        name_change_end = name_change_layout.currentWidget()

        # Change the name in UI & (try to) save changes
        name_edit.setText("")
        qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Error is displayed
        name_error = name_wrapper.layout().itemAt(1).widget()
        assert (
            name_error.text() == "Missing conversion method name"
        ), "Error is displayed"

        # Changes are not saved in DB
        method = pydive_db.conversionmethods_get()[1]
        assert method.name != "", "Name is not modified to empty"

    def test_settings_method_edit_suffix(self, pydive_settings, pydive_db, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get suffix-related widgets
        suffix_wrapper = methodListLayout.itemAtPosition(1, 2).widget()
        suffix_stack = suffix_wrapper.layout().itemAt(0).widget()
        suffix_label = suffix_stack.layout().currentWidget()

        suffix_change_layout = methodListLayout.itemAtPosition(1, 3).widget().layout()
        suffix_change_start = suffix_change_layout.currentWidget()

        # Display edit fields
        with qtbot.waitSignal(suffix_change_start.clicked, timeout=1000):
            qtbot.mouseClick(suffix_change_start, Qt.LeftButton)

        # Suffix is now editable & contains the suffix of the dive log
        suffix_edit = suffix_stack.layout().currentWidget()
        assert isinstance(
            suffix_edit, QtWidgets.QLineEdit
        ), "Suffix edit field now displayed"
        assert (
            suffix_edit.text() == suffix_label.text()
        ), "Suffix edit field contains the dive log's suffix"

        # Suffix edit button changed
        suffix_change_end = suffix_change_layout.currentWidget()
        assert (
            suffix_change_start != suffix_change_end
        ), "Edit button replaced by Save button"

        # Change the suffix in UI & save changes
        suffix_edit.setText("DTU")
        with qtbot.waitSignal(suffix_change_end.clicked, timeout=1000):
            qtbot.mouseClick(suffix_change_end, Qt.LeftButton)

        # Changes are saved in DB
        method = pydive_db.conversionmethods_get_by_name("DarkTherapee")
        assert method.suffix == "DTU", "Suffix is updated in database"

        # Display is back to initial state
        suffix_widget = suffix_stack.layout().currentWidget()
        assert suffix_widget == suffix_label, "Saving displays the suffix as QLabel"
        assert suffix_label.text() == "DTU", "Suffix is updated on display"

        suffix_change_widget = suffix_change_layout.currentWidget()
        assert (
            suffix_change_widget == suffix_change_start
        ), "Save button replaced by Edit button"

    def test_settings_method_edit_command(self, pydive_settings, pydive_db, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get command-related widgets
        command_wrapper = methodListLayout.itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()
        command_label = command_stack.layout().currentWidget()

        command_change_layout = methodListLayout.itemAtPosition(1, 5).widget().layout()
        command_change_start = command_change_layout.currentWidget()

        # Display edit fields
        with qtbot.waitSignal(command_change_start.clicked, timeout=1000):
            qtbot.mouseClick(command_change_start, Qt.LeftButton)

        # Command is now editable & contains the command of the dive log
        command_edit = command_stack.layout().currentWidget()
        assert isinstance(
            command_edit, QtWidgets.QLineEdit
        ), "Command edit field now displayed"
        assert (
            command_edit.text() == command_label.text()
        ), "Command edit field contains the dive log's command"

        # Command edit button changed
        command_change_end = command_change_layout.currentWidget()
        assert (
            command_change_start != command_change_end
        ), "Edit button replaced by Save button"

        # Change the command in UI & save changes
        command_edit.setText("../conversion.py -type DT")
        with qtbot.waitSignal(command_change_end.clicked, timeout=1000):
            qtbot.mouseClick(command_change_end, Qt.LeftButton)

        # Changes are saved in DB
        method = pydive_db.conversionmethods_get_by_name("DarkTherapee")
        assert (
            method.command == "../conversion.py -type DT"
        ), "Command is updated in database"

        # Display is back to initial state
        command_widget = command_stack.layout().currentWidget()
        assert command_widget == command_label, "Saving displays the command as QLabel"
        assert (
            command_label.text() == "../conversion.py -type DT"
        ), "Command is updated on display"

        command_change_widget = command_change_layout.currentWidget()
        assert (
            command_change_widget == command_change_start
        ), "Save button replaced by Edit button"

    def test_settings_method_edit_command_empty_error(
        self, pydive_settings, pydive_db, qtbot
    ):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get command-related widgets
        command_wrapper = methodListLayout.itemAtPosition(1, 4).widget()
        command_stack = command_wrapper.layout().itemAt(0).widget()

        command_change_layout = methodListLayout.itemAtPosition(1, 5).widget().layout()
        command_change_start = command_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(command_change_start, Qt.LeftButton)

        # Empty command field and validate
        command_edit = command_stack.layout().currentWidget()
        command_edit.setText("")
        command_change_end = command_change_layout.currentWidget()
        qtbot.mouseClick(command_change_end, Qt.LeftButton)
        # This checks part of the code where the same field has 2 errors in a row
        qtbot.mouseClick(command_change_end, Qt.LeftButton)

        # Error is displayed
        command_error = command_wrapper.layout().itemAt(1).widget()
        assert (
            command_error.text() == "Missing conversion method command"
        ), "Error is displayed"

        # Changes are not saved in DB
        method = pydive_db.conversionmethods_get()[1]
        assert method.command != "", "Command is not modified to empty"

    def test_settings_method_delete_cancel(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get delete button
        delete_widget = methodListLayout.itemAtPosition(1, 6).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.No
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        method = pydive_db.conversionmethods_get_by_name("DarkTherapee")
        assert method.name == "DarkTherapee", "Conversion method still exists"

    def test_settings_method_delete_confirm(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Get delete button
        delete_widget = methodListLayout.itemAtPosition(1, 6).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            pydive_db.conversionmethods_get_by_name("DarkTherapee")

        # Location no longer visible in UI
        name = methodListLayout.itemAtPosition(1, 0)
        assert name is None, "Method is deleted from UI"

    def test_settings_method_add_ok(self, pydive_settings, pydive_db, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Click "Add new"
        add_new = methodListLayout.itemAtPosition(3, 1).widget()
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = methodListLayout.itemAtPosition(3, 0).widget()
        name_edit = name_wrapper.layout().itemAt(0).widget()
        suffix_wrapper = methodListLayout.itemAtPosition(3, 2).widget()
        suffix_edit = suffix_wrapper.layout().itemAt(0).widget()
        command_wrapper = methodListLayout.itemAtPosition(3, 4).widget()
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
        save_button = methodListLayout.itemAtPosition(3, 6).widget()
        qtbot.mouseClick(save_button, Qt.LeftButton)

        # Data is saved in DB
        method = pydive_db.conversionmethods_get_by_name(fields["name"])
        assert method.suffix == fields["suffix"], "Suffix is saved in DB"
        assert method.command == fields["command"], "Command is saved in DB"

        # Check display of the new command
        assert methodListLayout.rowCount() == 5, "Row count is correct"
        for column, field in enumerate(fields.keys()):
            wrapper = methodListLayout.itemAtPosition(3, column * 2).widget()
            stack = wrapper.layout().itemAt(0).widget()
            label = stack.layout().currentWidget()
            assert label.text() == fields[field], "Data is displayed properly"

    def test_settings_method_add_with_errors(self, pydive_settings, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Click "Add new"
        add_new = methodListLayout.itemAtPosition(3, 1).widget()
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = methodListLayout.itemAtPosition(3, 0).widget()
        name_edit = name_wrapper.layout().itemAt(0).widget()
        command_wrapper = methodListLayout.itemAtPosition(3, 4).widget()
        command_edit = command_wrapper.layout().itemAt(0).widget()

        # Save with blank fields & check errors
        save_button = methodListLayout.itemAtPosition(3, 6).widget()
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.layout().itemAt(1) is not None, "Name error is displayed"
        name_error = name_wrapper.layout().itemAt(1).widget()
        assert (
            name_error.text() == "Missing conversion method name"
        ), "Name error displays correct error"

        assert (
            command_wrapper.layout().itemAt(1) is not None
        ), "Command error is displayed"
        command_error = command_wrapper.layout().itemAt(1).widget()
        assert (
            command_error.text() == "Missing conversion method command"
        ), "Command error displays correct error"

        # Click "Add new", all errors should be hidden
        qtbot.mouseClick(add_new, Qt.LeftButton)
        name_wrapper = methodListLayout.itemAtPosition(3, 0).widget()
        name_layout = name_wrapper.layout()
        name_edit = name_layout.itemAt(0).widget()
        command_wrapper = methodListLayout.itemAtPosition(3, 4).widget()
        command_layout = command_wrapper.layout()
        command_edit = command_layout.itemAt(0).widget()

        assert name_layout.itemAt(1) is None, "Name error is hidden"
        assert command_layout.itemAt(1) is None, "Command error is hidden"

        # Enter name, check error is hidden now
        name_edit.setText("New method")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_layout.itemAt(1) is None, "Name error is hidden"
        assert command_layout.itemAt(1) is not None, "Command error is displayed"

        # Enter command, empty name, check error is hidden now
        name_edit.setText("")
        command_edit.setText("../command_to_convert")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_layout.itemAt(1) is not None, "Name error is displayed"
        assert command_layout.itemAt(1) is None, "Command error is hidden"

    def test_settings_method_add_new_twice(self, pydive_settings, qtbot):
        methodListLayout = pydive_settings.layout().itemAt(7).widget().layout()

        # Click "Add new" twice
        add_new = methodListLayout.itemAtPosition(3, 1).widget()
        qtbot.mouseClick(add_new, Qt.LeftButton)
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # "New location" fields are visible only once
        assert methodListLayout.rowCount() == 5, "Only 1 line is added"

    def test_settings_category_list_display(self, pydive_settings, pydive_db):
        category = pydive_db.category_get_by_name("Top")
        categoryListTitle = pydive_settings.layout().itemAt(9).widget()
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Check overall structure
        assert categoryListTitle.text() == "Categories", "Categories title display"
        assert (
            categoryListLayout.columnCount() == 6
        ), "Categories have the right number of colums"
        assert (
            categoryListLayout.rowCount() == 4
        ), "Categories have the right number of rows"

        # Check name display
        name_wrapper_layout = categoryListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == category.name
        ), "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = categoryListLayout.itemAtPosition(1, 1).widget()
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check relative path display
        rel_path_wrapper_layout = (
            categoryListLayout.itemAtPosition(1, 2).widget().layout()
        )
        rel_path_layout = rel_path_wrapper_layout.itemAt(0).widget().layout()
        rel_path_label = rel_path_layout.currentWidget()
        assert isinstance(
            rel_path_label, QtWidgets.QLabel
        ), "Relative path field is a QLabel"
        assert (
            rel_path_label.text() == category.relative_path
        ), "Relative path field displays the expected data"

        # Check "change relative path" display
        change_rel_path_widget = categoryListLayout.itemAtPosition(1, 3).widget()
        change_rel_path_button = change_rel_path_widget.layout().currentWidget()
        assert isinstance(
            change_rel_path_widget, QtWidgets.QWidget
        ), "Change relative path field is a QWidget"
        assert isinstance(
            change_rel_path_button, IconButton
        ), "Change relative path button is a IconButton"

        # Check Icon display
        icon_wrapper_layout = categoryListLayout.itemAtPosition(1, 4).widget().layout()
        icon_widget = icon_wrapper_layout.itemAt(0).widget()
        assert isinstance(icon_widget, IconButton), "Icon field is a IconButton"
        assert (
            icon_widget.target == category.icon_path
        ), "Icon field has the right target"

        # Check Delete display
        delete_widget = categoryListLayout.itemAtPosition(1, 5).widget()
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

        # Check "Add new" display
        add_new_widget = categoryListLayout.itemAtPosition(3, 1).widget()
        assert isinstance(add_new_widget, IconButton), "Add new button is a IconButton"

    def test_settings_category_list_edit_name(self, pydive_settings, pydive_db, qtbot):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get name-related widgets
        name_wrapper_layout = categoryListLayout.itemAtPosition(1, 0).widget().layout()
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()

        name_change_layout = categoryListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        with qtbot.waitSignal(name_change_start.clicked, timeout=1000):
            qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Name is now editable & contains the name of the category
        name_edit = name_layout.currentWidget()
        assert isinstance(
            name_edit, QtWidgets.QLineEdit
        ), "Name edit field now displayed"
        assert (
            name_edit.text() == name_label.text()
        ), "Name edit field contains the category's name"

        # Name edit button changed
        name_change_end = name_change_layout.currentWidget()
        assert (
            name_change_start != name_change_end
        ), "Edit button replaced by Save button"

        # Change the name in UI & save changes
        name_edit.setText("WIP")
        with qtbot.waitSignal(name_change_end.clicked, timeout=1000):
            qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Changes are saved in DB
        category = pydive_db.category_get_by_name("WIP")
        assert category.name == "WIP", "Name is updated in database"

        # Display is back to initial state
        name_widget = name_layout.currentWidget()
        assert name_widget == name_label, "Saving displays the name as QLabel"
        assert name_label.text() == "WIP", "Name is updated on display"

        name_change_widget = name_change_layout.currentWidget()
        assert (
            name_change_widget == name_change_start
        ), "Save button replaced by Edit button"

    def test_settings_category_list_edit_name_error(
        self, pydive_settings, pydive_db, qtbot
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get name-related widgets
        name_wrapper_layout = categoryListLayout.itemAtPosition(1, 0).widget().layout()
        name_change_layout = categoryListLayout.itemAtPosition(1, 1).widget().layout()
        name_change_start = name_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(name_change_start, Qt.LeftButton)

        # Change the name
        name_edit = name_wrapper_layout.itemAt(0).widget().layout().currentWidget()
        name_edit.setText("")

        # Save changes
        name_change_end = name_change_layout.currentWidget()
        qtbot.mouseClick(name_change_end, Qt.LeftButton)
        # Triggered twice to test when errors were displayed before
        qtbot.mouseClick(name_change_end, Qt.LeftButton)

        # Check error is displayed
        error_widget = name_wrapper_layout.itemAt(1).widget()
        assert error_widget.text() == "Missing category name", "Error gets displayed"

        # Changes are not saved in DB
        category = pydive_db.category_get_by_name("Top")
        assert category.name != "", "Name is not modified to empty"

    def test_settings_category_list_edit_rel_path(
        self, pydive_settings, pydive_db, qtbot
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get relative path-related widgets
        rel_path_wrapper_layout = (
            categoryListLayout.itemAtPosition(1, 2).widget().layout()
        )
        rel_path_layout = rel_path_wrapper_layout.itemAt(0).widget().layout()
        rel_path_label = rel_path_layout.currentWidget()

        rel_path_change_layout = (
            categoryListLayout.itemAtPosition(1, 3).widget().layout()
        )
        rel_path_change_start = rel_path_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(rel_path_change_start, Qt.LeftButton)

        # Relative path is now editable & contains the relative path of the category
        rel_path_edit = rel_path_layout.currentWidget()
        assert isinstance(
            rel_path_edit, QtWidgets.QLineEdit
        ), "Relative path edit field now displayed"
        assert (
            rel_path_edit.text() == rel_path_label.text()
        ), "Relative path edit field contains the category's relative path"

        # Relative path edit button changed
        rel_path_change_end = rel_path_change_layout.currentWidget()
        assert (
            rel_path_change_start != rel_path_change_end
        ), "Edit button replaced by Save button"

        # Change the relative path in UI & save changes
        rel_path_edit.setText("WIP")
        with qtbot.waitSignal(rel_path_change_end.clicked, timeout=1000):
            qtbot.mouseClick(rel_path_change_end, Qt.LeftButton)

        # Changes are saved in DB
        category = pydive_db.category_get_by_name("Top")
        assert category.relative_path == "WIP", "Name is updated in database"

        # Display is back to initial state
        rel_path_widget = rel_path_layout.currentWidget()
        assert rel_path_widget == rel_path_label, "Saving displays the name as QLabel"
        assert rel_path_label.text() == "WIP", "Name is updated on display"

        rel_path_change_widget = rel_path_change_layout.currentWidget()
        assert (
            rel_path_change_widget == rel_path_change_start
        ), "Save button replaced by Edit button"

    def test_settings_category_list_edit_rel_path_error(
        self, pydive_settings, pydive_db, qtbot
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get relative path-related widgets
        rel_path_wrapper_layout = (
            categoryListLayout.itemAtPosition(1, 2).widget().layout()
        )
        rel_path_layout = rel_path_wrapper_layout.itemAt(0).widget().layout()
        rel_path_label = rel_path_layout.currentWidget()

        rel_path_change_layout = (
            categoryListLayout.itemAtPosition(1, 3).widget().layout()
        )
        rel_path_change_start = rel_path_change_layout.currentWidget()

        # Display edit fields
        qtbot.mouseClick(rel_path_change_start, Qt.LeftButton)

        # Relative path is now editable & contains the relative path of the category
        rel_path_edit = rel_path_layout.currentWidget()
        assert isinstance(
            rel_path_edit, QtWidgets.QLineEdit
        ), "Relative path edit field now displayed"
        assert (
            rel_path_edit.text() == rel_path_label.text()
        ), "Relative path edit field contains the category's relative path"

        # Relative path edit button changed
        rel_path_change_end = rel_path_change_layout.currentWidget()
        assert (
            rel_path_change_start != rel_path_change_end
        ), "Edit button replaced by Save button"

        # Change the relative path in UI & save changes
        rel_path_edit.setText("")
        qtbot.mouseClick(rel_path_change_end, Qt.LeftButton)
        # Triggered twice to test when errors were displayed before
        qtbot.mouseClick(rel_path_change_end, Qt.LeftButton)

        # Check error is displayed
        error_widget = rel_path_wrapper_layout.itemAt(1).widget()
        assert (
            error_widget.text() == "Missing category relative_path"
        ), "Error gets displayed"

        # Changes are not saved in DB
        category = pydive_db.category_get_by_name("Top")
        assert category.relative_path != "", "Relative path is not modified to empty"

    def test_settings_category_list_edit_icon(self, pydive_settings, pydive_db):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get change icon button
        icon_wrapper = categoryListLayout.itemAtPosition(1, 4).widget()
        icon_widget = icon_wrapper.layout().itemAt(0).widget()
        assert icon_widget.target_type == "file", "Icon change looks for files"

        # Simulating the actual dialog is impossible (it's OS-provided)
        icon_path = os.path.join(BASE_DIR, "pydive", "assets", "images", "add.png")
        icon_widget.pathSelected.emit(icon_path)

        # Changes are saved in DB
        category = pydive_db.category_get_by_name("Top")
        assert category.icon_path == icon_path, "Icon path is updated in database"

        # Can't test the display of the icon, since it's hidden in QIcon
        pass

    def test_settings_category_list_edit_icon_errors(self, pydive_settings):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get change icon button
        icon_wrapper = categoryListLayout.itemAtPosition(1, 4).widget()
        icon_widget = icon_wrapper.layout().itemAt(0).widget()

        # Trigger error with empty path
        icon_widget.pathSelected.emit("")
        error_widget = icon_wrapper.layout().itemAt(1).widget()
        assert (
            error_widget.text() == "The selected icon is invalid"
        ), "Error gets displayed"

        # Trigger error with folder path
        icon_path = os.path.join(BASE_DIR, "pydive", "assets", "style")
        icon_widget.pathSelected.emit(icon_path)
        error_widget = icon_wrapper.layout().itemAt(1).widget()
        assert (
            error_widget.text() == "The selected icon is invalid"
        ), "Error gets displayed"

        # Trigger error with path too long
        # Most errors are caught by the test to display them, so this is a bit silly...
        icon_path = os.path.join(
            BASE_DIR,
            "pydive",
            "assets",
            "images",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            ".",
            "add.png",
        )
        icon_widget.pathSelected.emit(icon_path)
        error_widget = icon_wrapper.layout().itemAt(1).widget()
        assert (
            error_widget.text() == "Max length for category icon_path is 250 characters"
        ), "Error gets displayed"

    def test_settings_category_list_delete_cancel(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get delete button
        delete_widget = categoryListLayout.itemAtPosition(1, 4).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.No
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        category = pydive_db.category_get_by_name("Top")
        assert category.name == "Top", "Category still exists"

    def test_settings_category_list_delete_confirm(
        self, pydive_settings, pydive_db, qtbot, monkeypatch
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()

        # Get delete button
        delete_widget = categoryListLayout.itemAtPosition(2, 5).widget()

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        qtbot.mouseClick(delete_widget, Qt.LeftButton)
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            pydive_db.category_get_by_name("Sélection")

        # category no longer visible in UI
        name = categoryListLayout.itemAtPosition(2, 0)
        assert name is None, "Category is deleted from UI"

    def test_settings_category_list_add_category_display(self, pydive_settings, qtbot):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()
        last_row = categoryListLayout.rowCount() - 1

        # Get "add new" button
        add_new = categoryListLayout.itemAtPosition(last_row, 1).widget()

        # Display edit fields
        with qtbot.waitSignal(add_new.clicked, timeout=1000):
            qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are now displayed
        name_wrapper = categoryListLayout.itemAtPosition(last_row, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        assert isinstance(
            name_label, QtWidgets.QLineEdit
        ), "Add new - name is a QLineEdit"
        assert name_label.text() == "", "Add new - name field is empty"

        rel_path_wrapper = (
            categoryListLayout.itemAtPosition(last_row, 2).widget().layout()
        )
        rel_path_label = rel_path_wrapper.itemAt(0).widget()
        assert isinstance(
            rel_path_label, QtWidgets.QLineEdit
        ), "Add new - Relative path is a QLineEdit"
        assert rel_path_label.text() == "", "Add new - Relative path field is empty"

        icon_wrapper = categoryListLayout.itemAtPosition(last_row, 4).widget()
        icon_widget = icon_wrapper.layout().itemAt(0).widget()
        assert isinstance(
            icon_widget, PathSelectButton
        ), "Add new - Icon change is a PathSelectButton"

        save = categoryListLayout.itemAtPosition(last_row, 5).widget()
        assert isinstance(save, IconButton), "Add new - Save button is an IconButton"

    def test_settings_category_list_add_category_save(
        self, pydive_settings, pydive_db, qtbot
    ):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()
        last_row = categoryListLayout.rowCount() - 1

        # Get "add new" button
        add_new = categoryListLayout.itemAtPosition(last_row, 1).widget()

        # Display edit fields
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # Enter a new name
        name_wrapper = categoryListLayout.itemAtPosition(last_row, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        name_label.setText("New category")

        # Enter a new relative path
        rel_path_wrapper = (
            categoryListLayout.itemAtPosition(last_row, 2).widget().layout()
        )
        rel_path_label = rel_path_wrapper.itemAt(0).widget()
        rel_path_label.setText("A path")

        # Save changes
        save_button = categoryListLayout.itemAtPosition(last_row, 5).widget()
        qtbot.mouseClick(save_button, Qt.LeftButton)

        # Data is saved in DB
        category = pydive_db.category_get_by_name("New category")
        assert category.name == "New category", "Name is saved in database"
        assert category.relative_path == "A path", "Relative path is saved in database"

        # Display is now similar as other categories
        assert categoryListLayout.rowCount() == last_row + 2, "New line is added"

        # Check name display
        name_wrapper_layout = (
            categoryListLayout.itemAtPosition(last_row, 0).widget().layout()
        )
        name_layout = name_wrapper_layout.itemAt(0).widget().layout()
        name_label = name_layout.currentWidget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == category.name
        ), "Name field displays the expected data"

        # Check "change name" display
        change_name_widget = categoryListLayout.itemAtPosition(last_row, 1).widget()
        assert isinstance(
            change_name_widget, QtWidgets.QWidget
        ), "Change name field is a QWidget"
        change_name_button = change_name_widget.layout().currentWidget()
        assert isinstance(
            change_name_button, IconButton
        ), "Change name button is a IconButton"

        # Check rel_path display
        rel_path_wrapper = (
            categoryListLayout.itemAtPosition(last_row, 2).widget().layout()
        )
        rel_path_layout = rel_path_wrapper.itemAt(0).widget().layout()
        rel_path_label = rel_path_layout.currentWidget()
        assert isinstance(
            rel_path_label, QtWidgets.QLabel
        ), "Relative path field is a QLineEdit"
        assert (
            rel_path_label.text() == category.relative_path
        ), "Relative path field displays the expected data"

        # Check "change relative path" display
        icon_wrapper = categoryListLayout.itemAtPosition(last_row, 4).widget()
        icon_widget = icon_wrapper.layout().itemAt(0).widget()
        assert isinstance(
            icon_widget, PathSelectButton
        ), "Add new - Icon change is a PathSelectButton"

        # Check Delete display
        delete_widget = categoryListLayout.itemAtPosition(last_row, 5).widget()
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

    def test_settings_category_list_add_new_twice(self, pydive_settings, qtbot):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()
        last_row = categoryListLayout.rowCount() - 1

        # Get "add new" button
        add_new = categoryListLayout.itemAtPosition(last_row, 1).widget()

        # Display edit fields
        qtbot.mouseClick(add_new, Qt.LeftButton)
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # "New category" fields are visible only once
        assert categoryListLayout.rowCount() == last_row + 2, "Only 1 line is added"

    def test_settings_category_list_add_with_errors(self, pydive_settings, qtbot):
        categoryListLayout = pydive_settings.layout().itemAt(10).widget().layout()
        last_row = categoryListLayout.rowCount() - 1

        # Click "Add new"
        add_new = categoryListLayout.itemAtPosition(last_row, 1).widget()
        qtbot.mouseClick(add_new, Qt.LeftButton)

        # New fields are displayed
        name_wrapper = categoryListLayout.itemAtPosition(last_row, 0).widget().layout()
        name_label = name_wrapper.itemAt(0).widget()
        rel_path_wrapper = (
            categoryListLayout.itemAtPosition(last_row, 2).widget().layout()
        )
        rel_path_label = rel_path_wrapper.itemAt(0).widget()
        save_button = categoryListLayout.itemAtPosition(last_row, 5).widget()

        # Save with blank fields & check errors
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is not None, "Name error is displayed"
        name_error = name_wrapper.itemAt(1).widget()
        assert (
            name_error.text() == "Missing category name"
        ), "Name error displays correct error"

        assert (
            rel_path_wrapper.itemAt(1) is not None
        ), "Relative path error is displayed"
        rel_path_error = rel_path_wrapper.itemAt(1).widget()
        assert (
            rel_path_error.text() == "Missing category relative_path"
        ), "Relative path error displays correct error"

        # Click "Add new", all errors should be hidden
        qtbot.mouseClick(add_new, Qt.LeftButton)
        name_wrapper = categoryListLayout.itemAtPosition(last_row, 0).widget().layout()
        rel_path_wrapper = (
            categoryListLayout.itemAtPosition(last_row, 2).widget().layout()
        )
        rel_path_label = rel_path_wrapper.itemAt(0).widget()
        save_button = categoryListLayout.itemAtPosition(last_row, 5).widget()

        assert name_wrapper.itemAt(1) is None, "Name error is hidden"
        assert rel_path_wrapper.itemAt(1) is None, "Relative path error is hidden"

        # Enter name, check error is hidden now
        name_label = name_wrapper.itemAt(0).widget()
        name_label.setText("New category")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is None, "Name error is hidden"
        assert (
            rel_path_wrapper.itemAt(1) is not None
        ), "Relative path error is displayed"
        rel_path_error = rel_path_wrapper.itemAt(1).widget()
        assert (
            rel_path_error.text() == "Missing category relative_path"
        ), "Relative path error displays correct error"

        # Enter Relative path, empty name, check error is hidden now
        rel_path_label.setText("New relative path")
        name_label.setText("")
        qtbot.mouseClick(save_button, Qt.LeftButton)

        assert name_wrapper.itemAt(1) is not None, "Name error is displayed"
        name_error = name_wrapper.itemAt(1).widget()
        assert (
            name_error.text() == "Missing category name"
        ), "Name error displays correct error"
        assert rel_path_wrapper.itemAt(1) is None, "Relative path error is hidden"

        # Trigger error with invalid icon
        icon_wrapper = categoryListLayout.itemAtPosition(last_row, 4).widget()
        icon_widget = icon_wrapper.layout().itemAt(0).widget()
        icon_path = os.path.join(BASE_DIR, "pydive", "assets", "images")
        icon_widget.pathSelected.emit(icon_path)
        error_widget = icon_wrapper.layout().itemAt(1).widget()
        assert (
            error_widget.text() == "The selected icon is invalid"
        ), "Error gets displayed"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
