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
    def pydive_settings(self, pydive_mainwindow, pydive_db, pydive_fake_pictures):
        pydive_mainwindow.display_tab("Settings")
        self.all_files = pydive_fake_pictures

        self.items = {
            "Location": pydive_db.storagelocation_get_by_id(1),
            "Divelog": pydive_db.storagelocation_get_by_id(6),
            "Method": pydive_db.conversionmethods_get_by_id(1),
            "Category": pydive_db.category_get_by_id(1),
        }
        self.missing_data_error_label = {
            "Location": "Missing storage location ",
            "Divelog": "Missing storage location ",
            "Method": "Missing conversion method ",
            "Category": "Missing category ",
        }
        self.mandatory_fields = {
            "Location": ["name", "path"],
            "Divelog": ["name", "path"],
            "Method": ["name", "command"],
            "Category": ["name", "relative_path"],
        }
        self.text_fields = {
            "Location": ["name"],
            "Divelog": ["name"],
            "Method": ["name", "command"],
            "Category": ["name"],
        }
        self.pathselect_target_type = {
            "Location": "folder",
            "Divelog": "file",
            "Method": None,
            "Category": "file",
        }
        self.grid_size = {
            "Location": (7, 5),
            "Divelog": (2, 5),
            "Method": (4, 7),
            "Category": (4, 6),
        }

        yield pydive_mainwindow.layout.currentWidget()

    @pytest.fixture
    def pydive_ui(self, pydive_settings):
        def get_ui(element):
            # Where each element is in the grid
            if element.startswith("new_"):
                row = get_ui("list_layout").rowCount() - 2
            else:
                row = 1
            columns = {
                "name_wrapper_layout": {
                    "Location": 0,
                    "Divelog": 0,
                    "Method": 0,
                    "Category": 0,
                },
                "name_change": {
                    "Location": 1,
                    "Divelog": 1,
                    "Method": 1,
                    "Category": 1,
                },
                "path_wrapper_layout": {
                    "Location": 2,
                    "Divelog": 2,
                },
                "suffix_wrapper_layout": {
                    "Method": 2,
                },
                "suffix_change": {
                    "Method": 3,
                },
                "command_wrapper_layout": {
                    "Method": 4,
                },
                "command_change": {
                    "Method": 5,
                },
                "icon_button": {
                    "Category": 5,
                },
                "relative_path_wrapper_layout": {
                    "Category": 2,
                },
                "icon_wrapper_layout": {
                    "Category": 4,
                },
            }

            # Overall elements
            if element == "title":
                rows = {"Location": 0, "Divelog": 2, "Method": 4, "Category": 0}
                row = rows[self.tested_section]
                column = 2 if self.tested_section == "Category" else 0
                return pydive_settings.layout().itemAtPosition(row, column).widget()
            elif element == "list_layout":
                rows = {"Location": 1, "Divelog": 3, "Method": 5, "Category": 1}
                row = rows[self.tested_section]
                column = 2 if self.tested_section == "Category" else 0
                return (
                    pydive_settings.layout()
                    .itemAtPosition(row, column)
                    .widget()
                    .layout()
                )

            # Field wrapper layout
            elif element.endswith("_wrapper_layout"):
                element_key = element[4:] if element.startswith("new_") else element
                if self.tested_section not in columns[element_key]:
                    raise ValueError(f"{self.tested_section} have no {element}")
                column = columns[element_key][self.tested_section]
                return (
                    get_ui("list_layout").itemAtPosition(row, column).widget().layout()
                )

            # Text fields - everything except paths
            elif element.endswith("_field") and element != "path_field":
                field = element[: len(element) - 6]
                layout = get_ui(field + "_wrapper_layout").itemAt(0).widget().layout()
                return layout.currentWidget()

            # Text fields change - everything except paths
            elif element.endswith("_change"):
                element_key = element[4:] if element.startswith("new_") else element
                if self.tested_section not in columns[element_key]:
                    raise ValueError(f"{self.tested_section} have no {element}")
                column = columns[element_key][self.tested_section]
                wrapper = get_ui("list_layout").itemAtPosition(row, column).widget()
                return wrapper.layout().currentWidget()

            # Error fields
            elif element.endswith("_error"):
                layout = element.replace("_error", "_wrapper_layout")
                return get_ui(layout).itemAt(1).widget()

            # Path-related fields
            elif element == "path_field":
                return get_ui("path_wrapper_layout").itemAt(0).widget()
            elif element == "path_button":
                if self.tested_section in ["Method", "Category"]:
                    raise ValueError(f"{self.tested_section} have no path field")
                return get_ui("list_layout").itemAtPosition(1, 3).widget()
            elif element == "new_path_button":
                return get_ui("list_layout").itemAtPosition(row, 3).widget()

            # Icon-related fields
            elif element == "icon_button":
                return get_ui("icon_wrapper_layout").itemAt(0).widget()

            # Elements for new items
            elif element in [
                "new_name",
                "new_path",
                "new_suffix",
                "new_command",
                "new_relative_path",
                "new_icon",
            ]:
                return get_ui(element + "_wrapper_layout").itemAt(0).widget()

            # Delete
            elif element == "delete":
                if self.tested_section == "Divelog":
                    raise ValueError(f"{self.tested_section} has no delete button")
                columns = {"Location": 4, "Method": 6, "Category": 5}
                column = columns[self.tested_section]
                return get_ui("list_layout").itemAtPosition(1, column).widget()

            # Add new - Name-related fields
            elif element == "add_new":
                row = get_ui("list_layout").rowCount() - 1
                return get_ui("list_layout").itemAtPosition(row, 1).widget()

            # Add new - Save
            elif element == "new_save":
                if self.tested_section == "Divelog":
                    raise ValueError(f"{self.tested_section} has no delete button")
                columns = {"Location": 4, "Method": 6, "Category": 5}
                column = columns[self.tested_section]
                return get_ui("list_layout").itemAtPosition(row, column).widget()

            else:
                raise ValueError("Field cound not be found")

        return get_ui

    def test_settings_display(self, pydive_settings):
        # Check overall structure
        assert (
            pydive_settings.layout().rowCount() == 6
        ), "Overall screen - Number of rows"
        assert (
            pydive_settings.layout().columnCount() == 3
        ), "Overall screen - Number of columns"

    @pytest.mark.parametrize("section", ["Location", "Divelog", "Method", "Category"])
    def test_settings_lists_display(self, pydive_db, pydive_ui, section):
        self.tested_section = section
        item = self.items[section]
        title = {
            "Location": "Image folders",
            "Divelog": "Dive log file",
            "Method": "Conversion methods",
            "Category": "Categories",
        }[section]
        grid_size = self.grid_size[section]
        target_type = self.pathselect_target_type[section]

        # Check overall structure
        assert pydive_ui("title").text() == title, f"{section} - Title display"
        assert (
            pydive_ui("list_layout").rowCount() == grid_size[0]
        ), f"{section} - Number of rows"
        assert (
            pydive_ui("list_layout").columnCount() == grid_size[1]
        ), f"{section} - Number of columns"

        # Check name-related fields
        assert isinstance(
            pydive_ui("name_field"), QtWidgets.QLabel
        ), f"{section} - Name field type"
        assert (
            pydive_ui("name_field").text() == item.name
        ), f"{section} - Name field data"
        assert isinstance(
            pydive_ui("name_change"), IconButton
        ), f"{section} - Name field change button type"

        # Check path display
        if section in ["Location", "Divelog"]:
            assert isinstance(
                pydive_ui("path_field"), QtWidgets.QLineEdit
            ), f"{section} - Path field type"
            assert (
                pydive_ui("path_field").text() == item.path
            ), f"{section} - Path field data"
            assert isinstance(
                pydive_ui("path_button"), PathSelectButton
            ), f"{section} - Path field change button type"
            assert (
                pydive_ui("path_button").target_type == target_type
            ), f"{section} - Path field change target type"
            assert (
                pydive_ui("path_button").target == item.path
            ), f"{section} - Path field change target"

        # Check suffix & command display
        if section == "Method":
            for field in ["suffix", "command"]:
                assert isinstance(
                    pydive_ui(field + "_field"), QtWidgets.QLabel
                ), f"{section} - {field} field type"
                assert pydive_ui(field + "_field").text() == getattr(
                    item, field
                ), f"{section} - {field} field data"
                assert isinstance(
                    pydive_ui(field + "_change"), IconButton
                ), f"{section} - {field} field change button type"

        # Check icon display
        if section == "Category":
            assert isinstance(
                pydive_ui("icon_button"), PathSelectButton
            ), f"{section} - Icon field type"
            assert (
                pydive_ui("icon_button").target_type == target_type
            ), f"{section} - Icon field target type"
            assert (
                pydive_ui("icon_button").target == item.icon
            ), f"{section} - Icon field target"

        # Check delete & add new display
        if section != "Divelog":
            assert isinstance(
                pydive_ui("delete"), IconButton
            ), "Delete button is a IconButton"
            assert isinstance(
                pydive_ui("add_new"), IconButton
            ), "Add new button is a IconButton"

    @pytest.mark.parametrize("section", ["Location", "Divelog", "Method", "Category"])
    def test_settings_lists_edit_text_fields(
        self, pydive_db, pydive_ui, section, qtbot
    ):
        self.tested_section = section
        item = self.items[section]
        fields = self.text_fields[section]

        for field in fields:
            # Display edit fields
            label = pydive_ui(field + "_field")
            change_start = pydive_ui(field + "_change")
            qtbot.mouseClick(change_start, Qt.LeftButton)

            # The field is now editable & contains the data of the storage Location
            assert isinstance(
                pydive_ui(field + "_field"), QtWidgets.QLineEdit
            ), f"{section} - {field} edit field now displayed"
            assert (
                pydive_ui(field + "_field").text() == label.text()
            ), f"{section} - {field} edit field contains the right data"

            # Field edit button changed
            change_end = pydive_ui(field + "_change")
            assert (
                change_start != change_end
            ), f"{section} - Edit button replaced by Save button"

            # Change the data in UI & save changes
            pydive_ui(field + "_field").setText("SD Card")
            qtbot.mouseClick(change_end, Qt.LeftButton)

            # Changes are saved in DB
            assert (
                getattr(item, field) == "SD Card"
            ), f"{section} - {field} is updated in database"

            # Display is back to initial state
            widget = pydive_ui(field + "_field")
            assert (
                widget == label
            ), f"{section} - Saving shows the {field} as the original QLabel"
            assert (
                pydive_ui(field + "_field").text() == "SD Card"
            ), f"{section} - {field} is updated on display"

            assert (
                pydive_ui(field + "_change") == change_start
            ), f"{section} - Save button replaced by Edit button"

    @pytest.mark.parametrize("section", ["Location", "Divelog", "Method", "Category"])
    def test_settings_lists_edit_text_fields_error(
        self, pydive_db, pydive_ui, section, qtbot
    ):
        self.tested_section = section
        item = self.items[section]
        error_label = self.missing_data_error_label[section]
        mandatory_fields = [
            f for f in self.mandatory_fields[section] if f in self.text_fields[section]
        ]

        # Display name edit fields
        qtbot.mouseClick(pydive_ui("name_change"), Qt.LeftButton)

        # Change the name
        pydive_ui("name_field").setText("")

        # Save changes
        qtbot.mouseClick(pydive_ui("name_change"), Qt.LeftButton)
        # Triggered twice to test when errors were displayed before
        qtbot.mouseClick(pydive_ui("name_change"), Qt.LeftButton)

        for field in mandatory_fields:
            # Display edit fields
            qtbot.mouseClick(pydive_ui(field + "_change"), Qt.LeftButton)

            # Change the data in UI & save changes
            pydive_ui(field + "_field").setText("")
            # Triggered twice to test when errors were displayed before
            pydive_ui(field + "_field").setText("")
            qtbot.mouseClick(pydive_ui(field + "_change"), Qt.LeftButton)

            # Check error is displayed
            assert (
                pydive_ui(field + "_error").text() == error_label + field
            ), f"{section} - {field} error gets displayed"

            # Changes are not saved in DB
            assert getattr(item, field) != "", f"{section} - {field} not changed in DB"

    @pytest.mark.parametrize("section", ["Location", "Divelog", "Category"])
    def test_settings_lists_edit_path_fields(
        self, pydive_db, pydive_ui, section, qtbot
    ):
        self.tested_section = section
        item = self.items[section]
        target_type = self.pathselect_target_type[section]
        field = "path" if section in ["Location", "Divelog"] else "icon"

        # Get change path button
        assert (
            pydive_ui(field + "_button").target_type == target_type
        ), f"{section} - {field} change looks for {target_type}"

        # Simulating the actual dialog is impossible (it's OS-provided)
        path = os.path.join(BASE_DIR, "pydive", "assets", "images", "add.png")
        pydive_ui(field + "_button").pathSelected.emit(path)

        # Changes are saved in DB & displayed on screen
        if target_type == "folder":
            new_path = os.path.join(path, "")
        else:
            new_path = path
        assert (
            getattr(item, field) == new_path
        ), f"{section} - {field} updated in database"
        if section != "Category":
            # The icon display for category can't be tested (not display anywhere)
            assert (
                pydive_ui(field + "_field").text() == path
            ), f"{section} - {field} updated on display"

    @pytest.mark.parametrize("section", ["Location", "Divelog"])
    def test_settings_lists_edit_path_error(self, pydive_ui, section):
        self.tested_section = section
        field = "path" if section in ["Location", "Divelog"] else "icon"
        error_label = self.missing_data_error_label[section]
        # Change path to empty value
        pydive_ui(field + "_button").pathSelected.emit("")

        # Error message is displayed
        assert (
            pydive_ui(field + "_error").text() == error_label + field
        ), f"{section} - {field} error gets displayed"

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_delete_cancel(
        self, pydive_ui, pydive_db, section, qtbot, monkeypatch
    ):
        self.tested_section = section

        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.No
        )
        qtbot.mouseClick(pydive_ui("delete"), Qt.LeftButton)
        # No assert needed - this will raise an exception if the element is deleted
        self.items[section]

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_delete_confirm(
        self, pydive_ui, section, pydive_db, qtbot, monkeypatch
    ):
        self.tested_section = section
        # Click delete, then "No" in the dialog
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        qtbot.mouseClick(pydive_ui("delete"), Qt.LeftButton)
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            {
                "Location": pydive_db.storagelocation_get_by_id(1),
                "Divelog": pydive_db.storagelocation_get_by_id(6),
                "Method": pydive_db.conversionmethods_get_by_id(1),
                "Category": pydive_db.category_get_by_id(1),
            }[section]

        # Item no longer visible in UI
        # Can't check rowCount because we don't reload the layout
        name = pydive_ui("list_layout").itemAtPosition(1, 0)
        assert name is None, f"{section} is deleted from UI"

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_add_new_display(self, pydive_ui, section, qtbot):
        self.tested_section = section
        # Display edit fields
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)

        grid_size = self.grid_size[section]
        target_type = self.pathselect_target_type[section]

        # Check overall structure
        assert (
            pydive_ui("list_layout").rowCount() == grid_size[0] + 1
        ), f"{section} - Number of rows"
        assert (
            pydive_ui("list_layout").columnCount() == grid_size[1]
        ), f"{section} - Number of columns"

        # Check name field
        assert isinstance(
            pydive_ui("new_name"), QtWidgets.QLineEdit
        ), f"{section} - Name field type"
        assert pydive_ui("new_name").text() == "", f"{section} - Name field data"

        # Check path field
        if section == "Location":
            assert isinstance(
                pydive_ui("new_path"), QtWidgets.QLineEdit
            ), f"{section} - Path field type"
            assert pydive_ui("new_path").text() == "", f"{section} - Path field data"
            assert isinstance(
                pydive_ui("new_path_button"), PathSelectButton
            ), f"{section} - Path field change button type"
            assert (
                pydive_ui("new_path_button").target_type == target_type
            ), f"{section} - Path field change target type"
            assert (
                pydive_ui("new_path_button").target == None
            ), f"{section} - Path field change target"

        # Check suffix & command display
        elif section == "Method":
            for field in ["suffix", "command"]:
                assert isinstance(
                    pydive_ui("new_" + field), QtWidgets.QLineEdit
                ), f"{section} - {field} field type"
                assert (
                    pydive_ui("new_" + field).text() == ""
                ), f"{section} - {field} field data"

        # Check icon display
        elif section == "Category":
            assert isinstance(
                pydive_ui("new_icon"), PathSelectButton
            ), f"{section} - Icon field type"
            assert (
                pydive_ui("new_icon").target_type == target_type
            ), f"{section} - Icon field target type"
            assert (
                pydive_ui("new_icon").target == None
            ), f"{section} - Icon field target"

        # Check save new display
        assert isinstance(
            pydive_ui("new_save"), IconButton
        ), "Save button is a IconButton"

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_save_new(self, pydive_ui, section, pydive_db, qtbot):
        self.tested_section = section
        grid_size = self.grid_size[section]
        target_type = self.pathselect_target_type[section]

        # Display Add new fields
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)

        # Enter data in the different fields
        fields = {
            "name": {"val": f"New {section}", "col": 0},
            "path": {"val": "/test_path/", "col": 2},
            "suffix": {"val": "NM", "col": 2},
            "command": {"val": "./new_method.py %TARGET_FILE%", "col": 4},
            "relative_path": {"val": "test_path", "col": 2},
            "icon": {
                "val": os.path.join(BASE_DIR, "pydive", "assets", "images", "add.png"),
                "col": 4,
            },
        }
        pydive_ui("new_name").setText(fields["name"]["val"])
        if section == "Location":
            pydive_ui("new_path_button").pathSelected.emit(fields["path"]["val"])
        if section == "Method":
            for field in ["suffix", "command"]:
                pydive_ui("new_" + field).setText(fields[field]["val"])
        elif section == "Category":
            pydive_ui("new_relative_path").setText(fields["relative_path"]["val"])
            pydive_ui("new_icon").pathSelected.emit(fields["icon"]["val"])
            # Since the button is not actually used, it doesn't update the .target
            # The "save_new" code will use the .target, and thus fail
            # In the location UI, the save part uses the QLineEdit field (updated at the same time)
            #   Hence it's not needed there
            pydive_ui("new_icon").target = fields["icon"]["val"]

        # Save all of that
        qtbot.mouseClick(pydive_ui("new_save"), Qt.LeftButton)

        # Number of rows is updated
        assert (
            pydive_ui("list_layout").rowCount() == grid_size[0] + 1
        ), f"{section} - New line is added"

        # The fixture is partly used after this point because not everything matches
        # Therefore, no reusability

        # Check text fields
        for field in ["name", "suffix", "command", "relative_path"]:
            if field in ["suffix", "command"] and section != "Method":
                continue
            elif field == "relative_path" and section != "Category":
                continue

            wrapper = (
                pydive_ui("list_layout")
                .itemAtPosition(grid_size[0] - 1, fields[field]["col"])
                .widget()
            )
            stack = wrapper.layout().itemAt(0).widget()
            label = stack.layout().currentWidget()
            assert label.text() == fields[field]["val"], f"{section} - {field} data"
            error = wrapper.layout().itemAt(1)
            assert error is None, f"{section} - {field} error is hidden"

            # Check "change field" display
            change_widget = (
                pydive_ui("list_layout")
                .itemAtPosition(grid_size[0] - 1, fields[field]["col"] + 1)
                .widget()
            )
            field_change = change_widget.layout().currentWidget()
            assert isinstance(
                field_change, IconButton
            ), f"{section} - Change {field} button type"

        # Check path fields
        field = "path"
        if section in ["Location", "Divelog"]:
            wrapper = (
                pydive_ui("list_layout")
                .itemAtPosition(grid_size[0] - 1, fields[field]["col"])
                .widget()
            )
            widget = wrapper.layout().itemAt(0).widget()
            assert widget.text() == fields[field]["val"], f"{section} - {field} data"
            error = wrapper.layout().itemAt(1)
            assert error is None, f"{section} - {field} error is hidden"

            # Check "change path" display
            change_widget = (
                pydive_ui("list_layout")
                .itemAtPosition(grid_size[0] - 1, fields[field]["col"] + 1)
                .widget()
            )
            assert isinstance(
                change_widget, PathSelectButton
            ), f"{section} - Change {field} button type"
            assert (
                change_widget.target_type == target_type
            ), f"{section} - Path field change target type"
            assert (
                change_widget.target == fields[field]["val"]
            ), f"{section} - Path field change target"

        # Check icon fields
        field = "icon"
        if section == "Category":
            wrapper = (
                pydive_ui("list_layout")
                .itemAtPosition(grid_size[0] - 1, fields[field]["col"])
                .widget()
            )
            widget = wrapper.layout().itemAt(0).widget()
            assert isinstance(
                widget, PathSelectButton
            ), f"{section} - Change {field} button type"
            assert widget.target_type == target_type, f"{section} - {field} target type"
            assert widget.target == fields[field]["val"], f"{section} - {field} target"

            error = wrapper.layout().itemAt(1)
            assert error is None, f"{section} - {field} error is hidden"

        # Check Delete display
        delete_widget = (
            pydive_ui("list_layout")
            .itemAtPosition(grid_size[0] - 1, grid_size[1] - 1)
            .widget()
        )
        assert isinstance(delete_widget, IconButton), "Delete button is a IconButton"

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_add_new_twice(self, pydive_ui, section, qtbot):
        self.tested_section = section
        # Click twice
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)

        grid_size = self.grid_size[section]

        # Check that a new row is added only once
        assert (
            pydive_ui("list_layout").rowCount() == grid_size[0] + 1
        ), f"{section} - Number of rows"
        assert (
            pydive_ui("list_layout").columnCount() == grid_size[1]
        ), f"{section} - Number of columns"

    @pytest.mark.parametrize("section", ["Location", "Method", "Category"])
    def test_settings_lists_add_missing_mandatory_data(self, pydive_ui, section, qtbot):
        self.tested_section = section
        error_label = self.missing_data_error_label[section]
        mandatory_fields = self.mandatory_fields[section]

        # Click "Add new"
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)

        # Save with blank fields & check errors
        qtbot.mouseClick(pydive_ui("new_save"), Qt.LeftButton)

        for field in mandatory_fields:
            assert (
                pydive_ui("new_" + field + "_error") is not None
            ), f"{section} - {field} error is displayed"
            assert (
                pydive_ui("new_" + field + "_error").text() == error_label + field
            ), f"{section} - {field} error display"

        # Click "Add new", all errors should be hidden
        qtbot.mouseClick(pydive_ui("add_new"), Qt.LeftButton)
        for field in mandatory_fields:
            with pytest.raises(AttributeError):
                pydive_ui("new_" + field + "_error")
                pytest.fail(f"{section} - {field} error is hidden")

        # Enter each field, then check it hides the corresponding error
        for field in mandatory_fields:
            # Empty all fields
            for any_field in mandatory_fields:
                if any_field == "path":
                    pydive_ui("new_path_button").pathSelected.emit("")
                else:
                    pydive_ui("new_" + any_field).setText("")
            # Enter just the one we want
            if field == "path":
                icon_path = os.path.join(
                    BASE_DIR, "pydive", "assets", "images", "add.png"
                )
                pydive_ui("new_path_button").pathSelected.emit(icon_path)
            else:
                pydive_ui("new_" + field).setText("New value")
            qtbot.mouseClick(pydive_ui("new_save"), Qt.LeftButton)

            # Check field error hidden
            with pytest.raises(AttributeError):
                pydive_ui("new_" + field + "_error")
                pytest.fail(f"{section} - {field} error is hidden")
            for other in [f for f in mandatory_fields if f != field]:
                assert (
                    pydive_ui("new_" + other + "_error") is not None
                ), f"{section} - {other} error is displayed"
                assert (
                    pydive_ui("new_" + other + "_error").text() == error_label + other
                ), f"{section} - {other} error display"

    def test_settings_category_list_edit_icon_error(self, pydive_ui):
        self.tested_section = "Category"

        paths = [
            "",
            ".",
            os.path.join(BASE_DIR, "pydive", "assets", "style", "app.css"),
        ]
        for path in paths:
            pydive_ui("icon_button").pathSelected.emit(path)
            # Empty path ==> error
            assert (
                pydive_ui("icon_error").text() == "The selected icon is invalid"
            ), "Category - Icon error gets displayed"

        # Path too long ==> error in DB only
        long_path = [BASE_DIR, "pydive", "assets", "images"] + ["."] * 200 + ["add.png"]
        long_path = os.path.join(*long_path)
        pydive_ui("icon_button").pathSelected.emit(long_path)
        assert (
            pydive_ui("icon_error").text()
            == "Max length for category icon is 250 characters"
        ), "Category - Icon error gets displayed"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
