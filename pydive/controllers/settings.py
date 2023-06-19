"""Settings screen: Define locations for picture storage, Subsurface file, ...

Classes
----------
SettingsController
    Settings screen: Define locations for picture storage, Subsurface file, ...
"""
import gettext

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.iconbutton import IconButton
import models.storagelocation
import models.conversionmethod
from models.base import ValidationException

_ = gettext.gettext


class LocationsList:
    """Displays locations & allows to modify them

    Attributes
    ----------
    columns : dict
        The columns to display in the grid
    parent_controller : SettingsController
        A reference to the parent controller
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this list

    Methods
    -------
    __init__ (parent_window)
        Stores reference to parent controller & defines UI elements.
    add_location_ui (location_model)
        Adds the fields for the provided location
    on_click_name_change
        Displays fields to modify the location name
    on_validate_name_change
        Saves the storage location name
    on_validate_path_change
        Saves the storage location path
    on_click_new_location
        Displays all the fields to create a new location
    on_validate_new_location
        Saves a new location
    refresh_display
        Updates the locations names & paths displayed on screen
    """

    columns = [
        {
            "name": _("Name"),
            "stretch": 10,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,
            "stretch": 1,
        },
        {
            "name": _("Path"),
            "stretch": 15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,
            "stretch": 1,
        },
        {
            "name": None,
            "stretch": 1,
        },
    ]

    def __init__(self, parent_controller):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()

        # Add headers
        for i, col in enumerate(self.columns):
            # Note: _ is added here again because, otherwise, it doesn't translate
            header = QtWidgets.QLabel(_(col["name"]))
            header.setProperty("class", "grid_header")
            if "alignment" in col:
                header.setAlignment(col["alignment"])
            self.ui["layout"].addWidget(header, 0, i)
            self.ui["layout"].setColumnStretch(i, col["stretch"])

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        self.ui["locations"] = {}
        self.new_location = None

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this list"""

        self.ui["locations"] = {}
        for location_model in self.database.storagelocations_get():
            self.add_location_ui(location_model)

        # Create new location
        self.ui["add_new"] = IconButton(
            QtGui.QIcon("assets/images/add.png"), "", self.ui["main"]
        )
        self.ui["add_new"].clicked.connect(lambda: self.on_click_new_location())

        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["locations"]) + 1, 1
        )

        self.refresh_display()
        return self.ui["main"]

    def add_location_ui(self, location_model):
        """Adds the fields for the provided location

        Parameters
        ----------
        location_model : models.storagelocation.StorageLocation
            The storage location to display
        """
        self.ui["locations"][location_model.id] = {}
        location = self.ui["locations"][location_model.id]
        location["model"] = location_model
        location["error"] = {}

        # Location name
        location["name"] = QtWidgets.QWidget()
        location["name_layout"] = QtWidgets.QStackedLayout()
        location["name"].setLayout(location["name_layout"])
        self.ui["layout"].addWidget(location["name"], len(self.ui["locations"]), 0)

        # Location name - Display
        location["name_label"] = QtWidgets.QLabel()
        location["name_layout"].insertWidget(0, location["name_label"])

        # Location name - Edit box
        location["name_edit"] = QtWidgets.QLineEdit()
        location["name_edit"].returnPressed.connect(
            lambda: self.on_validate_name_change(location_model.id)
        )
        location["name_layout"].insertWidget(1, location["name_edit"])

        # Location name - Edit / validate button
        location["name_change"] = QtWidgets.QWidget()
        location["name_change_layout"] = QtWidgets.QStackedLayout()
        location["name_change"].setLayout(location["name_change_layout"])
        self.ui["layout"].addWidget(
            location["name_change"], len(self.ui["locations"]), 1
        )

        # Location name - Edit button
        location["name_change_start"] = IconButton(
            QtGui.QIcon("assets/images/modify.png"), "", self.ui["main"]
        )
        location["name_change_start"].clicked.connect(
            lambda: self.on_click_name_change(location["model"].id)
        )
        location["name_change_layout"].insertWidget(0, location["name_change_start"])

        # Location name - Validate button
        location["name_change_end"] = IconButton(
            QtGui.QIcon("assets/images/done.png"), "", self.ui["main"]
        )
        location["name_change_end"].clicked.connect(
            lambda: self.on_validate_name_change(location["model"].id)
        )
        location["name_change_layout"].insertWidget(1, location["name_change_end"])

        # Location path
        location["path"] = QtWidgets.QLineEdit()
        location["path"].setEnabled(False)
        self.ui["layout"].addWidget(location["path"], len(self.ui["locations"]), 2)

        # Location path change
        location["path_change"] = PathSelectButton(
            QtGui.QIcon("assets/images/modify.png"), location_model.type.name
        )
        location["path_change"].pathSelected.connect(
            lambda a, location=location: self.on_validate_path_change(
                location["model"].id, a
            )
        )
        self.ui["layout"].addWidget(
            location["path_change"], len(self.ui["locations"]), 3
        )

        # Delete location
        location["delete"] = IconButton(
            QtGui.QIcon("assets/images/delete.png"), "", self.ui["main"]
        )
        location["delete"].clicked.connect(
            lambda a, location=location: self.on_click_delete_location(
                location["model"].id
            )
        )
        self.ui["layout"].addWidget(location["delete"], len(self.ui["locations"]), 4)

    def on_click_name_change(self, location_id):
        """Displays fields to modify the location name

        Parameters
        ----------
        location_id : int
            The ID of the location whose name needs to change
        """
        location = self.ui["locations"][location_id]

        # Update display
        location["name_edit"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(1)
        location["name_change_layout"].setCurrentIndex(1)

    def on_validate_name_change(self, location_id):
        """Saves the storage location name

        Parameters
        ----------
        location_id : int
            The ID of the location whose name needs to change
        """
        location = self.ui["locations"][location_id]
        # Save the change
        try:
            location["model"].name = location["name_edit"].text()
            self.database.session.add(location["model"])
            self.database.session.commit()
            self.clear_error(location_id, "name")
        except ValidationException as error:
            self.display_error(location["model"].id, "name", error.message)
            return

        # Update display
        location["name_label"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(0)
        location["name_change_layout"].setCurrentIndex(0)

    def on_validate_path_change(self, location_id, path):
        """Saves the storage location path

        Parameters
        ----------
        location_id : int
            The ID of the location whose path needs to change
        """
        location = self.ui["locations"][location_id]

        # Save the change (for existing models)
        if location_id:
            try:
                location["model"].path = path
                self.database.session.add(location["model"])
                self.database.session.commit()
                self.clear_error(location_id, "path")
            except ValidationException as error:
                self.display_error(location["model"].id, "path", error.message)
                return

        # Update display
        location["path"].setText(path)

    def on_click_new_location(self):
        """Displays all the fields to create a new location"""

        # Move the New button to another row
        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["locations"]) + 2, 1
        )

        # Create fields for new location
        if 0 in self.ui["locations"]:
            location = self.ui["locations"][0]
            if "error" in location:
                for i in location["error"]:
                    self.ui["layout"].removeWidget(location["error"][i])
                    location["error"][i].deleteLater()
                del location["error"]
            for i in location:
                self.ui["layout"].removeWidget(location[i])
                location[i].deleteLater()
            del self.ui["locations"][0]

        self.ui["locations"][0] = {}
        location = self.ui["locations"][0]
        location["error"] = {}

        # Location name
        location["name"] = QtWidgets.QLineEdit()
        self.ui["layout"].addWidget(location["name"], len(self.ui["locations"]), 0)

        # Location path
        location["path"] = QtWidgets.QLineEdit()
        location["path"].setEnabled(False)
        self.ui["layout"].addWidget(location["path"], len(self.ui["locations"]), 2)

        # Location path change
        # TODO: Settings screen > Allow to create locations of type "file" (for dive log)
        location["path_change"] = PathSelectButton(
            QtGui.QIcon("assets/images/modify.png"), "folder"
        )
        location["path_change"].pathSelected.connect(
            lambda a, location=location: self.on_validate_path_change(0, a)
        )
        self.ui["layout"].addWidget(
            location["path_change"], len(self.ui["locations"]), 3
        )

        # Location name - Validate button
        location["validate_new"] = IconButton(
            QtGui.QIcon("assets/images/done.png"), "", self.ui["main"]
        )
        location["validate_new"].clicked.connect(self.on_validate_new_location)
        self.ui["layout"].addWidget(
            location["validate_new"], len(self.ui["locations"]), 4
        )

    def on_validate_new_location(self):
        """Saves a new location"""
        location = self.ui["locations"][0]

        if not self.new_location:
            self.new_location = models.storagelocation.StorageLocation()

        # Clear previous errors
        for i in location["error"]:
            self.ui["layout"].removeWidget(location["error"][i])
            location["error"][i].deleteLater()
        location["error"] = {}

        # Apply values in each field
        # TODO: Settings screen > Allow to create locations of type "file" (for dive log)
        self.new_location.type = "folder"
        for field in ["name", "path"]:
            try:
                setattr(self.new_location, field, location[field].text())
                self.clear_error(0, field)
            except ValidationException as error:
                self.display_error(0, field, error.message)

        if location["error"]:
            return

        self.database.session.add(self.new_location)
        self.database.session.commit()

        # Remove all "new location" fields (error fields were removed before)
        self.ui["layout"].removeWidget(location["name"])
        self.ui["layout"].removeWidget(location["path"])
        self.ui["layout"].removeWidget(location["path_change"])
        self.ui["layout"].removeWidget(location["validate_new"])
        location["name"].deleteLater()
        location["path"].deleteLater()
        location["path_change"].deleteLater()
        location["validate_new"].deleteLater()
        del location["name"]
        del location["path"]
        del location["path_change"]
        del location["validate_new"]
        del self.ui["locations"][0]

        # Add fields for the newly created location (as "normal" fields)
        self.add_location_ui(self.new_location)
        self.refresh_display()
        self.new_location = None

        # Move the "add new" button
        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["locations"]) + 1, 1
        )

    def on_click_delete_location(self, location_id):
        """Handler for delete button: deletes the location & refreshes the screen

        Parameters
        ----------
        location_id : int
            The ID of the location which should be deleted
        """
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle("Please confirm")
        dialog.setText("Do you really want to delete this storage location?")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            location = self.ui["locations"][location_id]
            self.database.delete(location["model"])
            del location["model"]
            # Delete all the corresponding fields
            if "error" in location:
                for i in location["error"]:
                    self.ui["layout"].removeWidget(location["error"][i])
                    location["error"][i].deleteLater()
                del location["error"]
            for i in location:
                if "layout" not in i:
                    self.ui["layout"].removeWidget(location[i])
                    location[i].deleteLater()
            del self.ui["locations"][location_id]

    def display_error(self, location_id, field, message):
        """Displays an error for the provided field

        Parameters
        ----------
        location_id : int
            The ID of the modified location (0 for new locations)
        field : str
            The name of the field for which to clear the error
        message : str
            The error to display
        """
        location = self.ui["locations"][location_id]
        if field in location["error"]:
            location["error"][field].setText(message)
        else:
            location["error"][field] = QtWidgets.QLabel(message)
            location["error"][field].setProperty("class", "validation_error")
            column = 0 if field == "name" else 2
            row = (
                len(self.ui["locations"])
                if location_id == 0
                else len(
                    [p for p in self.ui["locations"] if p <= location_id and p != 0]
                )
            )
            self.ui["layout"].addWidget(
                location["error"][field],
                row,
                column,
                QtCore.Qt.AlignBottom,
            )

    def clear_error(self, location_id, field):
        """Hides the error that was displayed for the provided field

        Parameters
        ----------
        location_id : int
            The ID of the modified location (0 for new locations)
        field : str
            The name of the field for which to clear the error
        """
        location = self.ui["locations"][location_id]
        if field in location["error"]:
            location["error"][field].setText("")

    def refresh_display(self):
        """Updates the locations names & paths displayed on screen"""

        # Refresh list of locations
        for location in self.ui["locations"].values():
            location["name_label"].setText(location["model"].name)
            location["name_edit"].setText(location["model"].name)
            location["path"].setText(location["model"].path)
            location["path_change"].target = location["model"].path


class ConversionMethodsList:
    """Displays conversion methods & allows to modify them

    Attributes
    ----------
    columns : dict
        The columns to display in the grid
    parent_controller : SettingsController
        A reference to the parent controller
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this list

    Methods
    -------
    __init__ (parent_window)
        Stores reference to parent controller & defines UI elements.
    add_method_ui (method_model)
        Adds the fields for the provided conversion method
    on_click_field_change
        Displays fields to modify the conversion method name
    on_validate_field_change
        Saves the storage conversion method name
    on_click_new_method
        Displays all the fields to create a new conversion method
    on_validate_new_method
        Saves a new conversion method
    refresh_display
        Updates the conversion methods names & commands displayed on screen
    """

    columns = [
        {
            "name": _("Name"),
            "stretch": 10,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,
            "stretch": 1,
        },
        {
            "name": _("File name suffix"),
            "stretch": 2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,
            "stretch": 1,
        },
        {
            "name": _("Command to execute"),
            "stretch": 15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,
            "stretch": 1,
        },
        {
            "name": None,
            "stretch": 1,
        },
    ]

    conversion_method_help = _(
        """Enter the command to run to generate the target file (from a raw file)
%SOURCE_FILE% will be replaced by the source file's full path
%TARGET_FILE% will be replaced by the target file's full path
%TARGET_FOLDER% will be replaced by the target file's folder path"""
    )

    def __init__(self, parent_controller):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()

        # Add headers
        for i, col in enumerate(self.columns):
            # Note: _ is added here again because, otherwise, it doesn't translate
            header = QtWidgets.QLabel(_(col["name"]))
            header.setProperty("class", "grid_header")
            if "alignment" in col:
                header.setAlignment(col["alignment"])
            self.ui["layout"].addWidget(header, 0, i)
            self.ui["layout"].setColumnStretch(i, col["stretch"])

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        self.ui["methods"] = {}
        self.new_method = None

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this list"""

        self.ui["methods"] = {}
        for method_model in self.database.conversionmethods_get():
            self.add_method_ui(method_model)

        # Create new conversion method
        self.ui["add_new"] = IconButton(
            QtGui.QIcon("assets/images/add.png"), "", self.ui["main"]
        )
        self.ui["add_new"].clicked.connect(lambda: self.on_click_new_method())

        self.ui["layout"].addWidget(self.ui["add_new"], len(self.ui["methods"]) + 1, 1)

        self.refresh_display()
        return self.ui["main"]

    def add_method_ui(self, method_model):
        """Adds the fields for the provided conversion method

        Parameters
        ----------
        method_model : models.conversionmethod.ConversionMethod
            The conversion method to display
        """
        self.ui["methods"][method_model.id] = {}
        method = self.ui["methods"][method_model.id]
        method["model"] = method_model
        method["error"] = {}

        for column, field in enumerate(["name", "suffix", "command"]):
            # Layout for the grid cell
            method[field] = QtWidgets.QWidget()
            method[field + "_layout"] = QtWidgets.QStackedLayout()
            method[field].setLayout(method[field + "_layout"])
            self.ui["layout"].addWidget(
                method[field], len(self.ui["methods"]), column * 2
            )

            # Conversion method field - Display
            method[field + "_label"] = QtWidgets.QLabel()
            method[field + "_layout"].insertWidget(0, method[field + "_label"])

            # Conversion method field - Edit box
            method[field + "_edit"] = QtWidgets.QLineEdit()
            method[field + "_edit"].returnPressed.connect(
                lambda field=field: self.on_validate_field_change(
                    field, method_model.id
                )
            )
            method[field + "_layout"].insertWidget(1, method[field + "_edit"])

            # Conversion method field - Edit / validate button
            method[field + "_change"] = QtWidgets.QWidget()
            method[field + "_change_layout"] = QtWidgets.QStackedLayout()
            method[field + "_change"].setLayout(method[field + "_change_layout"])
            self.ui["layout"].addWidget(
                method[field + "_change"], len(self.ui["methods"]), column * 2 + 1
            )

            # Conversion method field - Edit button
            method[field + "_change_start"] = IconButton(
                QtGui.QIcon("assets/images/modify.png"), "", self.ui["main"]
            )
            method[field + "_change_start"].clicked.connect(
                lambda a, field=field: self.on_click_field_change(
                    field, method["model"].id
                )
            )
            method[field + "_change_layout"].insertWidget(
                0, method[field + "_change_start"]
            )

            # Conversion method field - Validate button
            method[field + "_change_end"] = IconButton(
                QtGui.QIcon("assets/images/done.png"), "", self.ui["main"]
            )
            method[field + "_change_end"].clicked.connect(
                lambda a, field=field: self.on_validate_field_change(
                    field, method["model"].id
                )
            )
            method[field + "_change_layout"].insertWidget(
                1, method[field + "_change_end"]
            )

        # Delete Conversion method
        method["delete"] = IconButton(
            QtGui.QIcon("assets/images/delete.png"), "", self.ui["main"]
        )
        method["delete"].clicked.connect(
            lambda a, method=method: self.on_click_delete_method(method["model"].id)
        )
        self.ui["layout"].addWidget(method["delete"], len(self.ui["methods"]), 6)

    def on_click_field_change(self, field, method_id):
        """Displays widgets to modify a given field the conversion method

        Parameters
        ----------
        field : str
            The field name to change (name, suffix or command)
        method_id : int
            The ID of the method whose name needs to change
        """
        method = self.ui["methods"][method_id]

        # Update display
        method[field + "_edit"].setText(getattr(method["model"], field))
        if field == "command":
            # Note: _ is added here again because, otherwise, it doesn't translate
            method[field + "_edit"].setToolTip(_(self.conversion_method_help))

        # Make widgets visible
        method[field + "_layout"].setCurrentIndex(1)
        method[field + "_change_layout"].setCurrentIndex(1)

    def on_validate_field_change(self, field, method_id):
        """Saves the modified field in the conversion method

        Parameters
        ----------
        field : str
            The field name to validate (name, suffix or command)
        method_id : int
            The ID of the method whose name needs to change
        """
        method = self.ui["methods"][method_id]
        # Save the change
        try:
            setattr(method["model"], field, method[field + "_edit"].text())
            self.database.session.add(method["model"])
            self.database.session.commit()
            self.clear_error(method_id, field)
        except ValidationException as error:
            self.display_error(method["model"].id, field, error.message)
            return

        # Update display
        method[field + "_label"].setText(getattr(method["model"], field))

        # Make widgets visible
        method[field + "_layout"].setCurrentIndex(0)
        method[field + "_change_layout"].setCurrentIndex(0)

    def on_click_new_method(self):
        """Displays all the fields to create a new method"""

        # Move the New button to another row
        self.ui["layout"].addWidget(self.ui["add_new"], len(self.ui["methods"]) + 2, 1)

        # Remove all existing fields
        if 0 in self.ui["methods"]:
            method = self.ui["methods"][0]
            if "error" in method:
                for i in method["error"]:
                    self.ui["layout"].removeWidget(method["error"][i])
                    method["error"][i].deleteLater()
                del method["error"]
            for i in method:
                self.ui["layout"].removeWidget(method[i])
                method[i].deleteLater()
            del self.ui["methods"][0]

        # Basic structure
        self.ui["methods"][0] = {}
        method = self.ui["methods"][0]
        method["error"] = {}

        # Add all modifiable fields
        for column, field in enumerate(["name", "suffix", "command"]):
            method[field] = QtWidgets.QLineEdit()
            self.ui["layout"].addWidget(
                method[field], len(self.ui["methods"]), column * 2
            )
        # Note: _ is added here again because, otherwise, it doesn't translate
        method["command"].setToolTip(_(self.conversion_method_help))

        # Validate button
        method["validate_new"] = IconButton(
            QtGui.QIcon("assets/images/done.png"), "", self.ui["main"]
        )
        method["validate_new"].clicked.connect(self.on_validate_new_method)
        self.ui["layout"].addWidget(method["validate_new"], len(self.ui["methods"]), 7)

    def on_validate_new_method(self):
        """Saves a new conversion method"""
        method = self.ui["methods"][0]

        if not self.new_method:
            self.new_method = models.conversionmethod.ConversionMethod()

        # Clear previous errors
        for i in method["error"]:
            self.ui["layout"].removeWidget(method["error"][i])
            method["error"][i].deleteLater()
        method["error"] = {}

        # Apply values in each field
        for field in ["name", "suffix", "command"]:
            try:
                setattr(self.new_method, field, method[field].text())
                self.clear_error(0, field)
            except ValidationException as error:
                self.display_error(0, field, error.message)

        if method["error"]:
            return

        self.database.session.add(self.new_method)
        self.database.session.commit()

        # Remove all "new method" fields (error fields were removed before)
        for field in ["name", "suffix", "command", "validate_new"]:
            self.ui["layout"].removeWidget(method[field])
            method[field].deleteLater()
            del method[field]
        del self.ui["methods"][0]

        # Add fields for the newly created method (as "normal" fields)
        self.add_method_ui(self.new_method)
        self.refresh_display()
        self.new_method = None

        # Move the "add new" button
        self.ui["layout"].addWidget(self.ui["add_new"], len(self.ui["methods"]) + 1, 1)

    def on_click_delete_method(self, method_id):
        """Handler for delete button: deletes the method & refreshes the screen

        Parameters
        ----------
        method_id : int
            The ID of the method which should be deleted
        """
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle(_("Please confirm"))
        dialog.setText(_("Do you really want to delete this conversion method?"))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            method = self.ui["methods"][method_id]
            self.database.delete(method["model"])
            del method["model"]
            # Delete all the corresponding fields
            if "error" in method:
                for i in method["error"]:
                    self.ui["layout"].removeWidget(method["error"][i])
                    method["error"][i].deleteLater()
                del method["error"]
            for i in method:
                if "layout" not in i:
                    self.ui["layout"].removeWidget(method[i])
                    method[i].deleteLater()
            del self.ui["methods"][method_id]

    def display_error(self, method_id, field, message):
        """Displays an error for the provided field

        Parameters
        ----------
        method_id : int
            The ID of the modified method (0 for new methods)
        field : str
            The name of the field for which to clear the error
        message : str
            The error to display
        """
        method = self.ui["methods"][method_id]
        if field in method["error"]:
            method["error"][field].setText(message)
        else:
            method["error"][field] = QtWidgets.QLabel(message)
            method["error"][field].setProperty("class", "validation_error")
            column = 0 if field == "name" else 2
            row = (
                len(self.ui["methods"])
                if method_id == 0
                else len([p for p in self.ui["methods"] if p <= method_id and p != 0])
            )
            self.ui["layout"].addWidget(
                method["error"][field],
                row,
                column,
                QtCore.Qt.AlignBottom,
            )

    def clear_error(self, method_id, field):
        """Hides the error that was displayed for the provided field

        Parameters
        ----------
        method_id : int
            The ID of the modified method (0 for new methods)
        field : str
            The name of the field for which to clear the error
        """
        method = self.ui["methods"][method_id]
        if field in method["error"]:
            method["error"][field].setText("")

    def refresh_display(self):
        """Updates the methods names & paths displayed on screen"""

        # Refresh list of methods
        for method in self.ui["methods"].values():
            for field in ["name", "suffix", "command"]:
                method[field + "_label"].setText(getattr(method["model"], field))


class SettingsController:
    """Settings screen: Define locations for picture storage, Subsurface file, ...

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
        The window displaying this controller
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this screen
    toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar

    Methods
    -------
    __init__ (parent_window)
        Stores reference to parent window & defines UI elements.
    add_location_ui (location_model)
        Adds the fields for the provided location
    on_click_name_change
        Displays fields to modify the location name
    on_validate_name_change
        Saves the storage location name
    on_validate_path_change
        Saves the storage location path
    on_click_new_location
        Displays all the fields to create a new location
    on_validate_new_location
        Saves a new location
    refresh_display
        Updates the locations names & paths displayed on screen
    """

    name = _("Settings")

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database
        self.locations_list = LocationsList(self)
        self.conversion_methods_list = ConversionMethodsList(self)
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        self.ui["locations_list_label"] = QtWidgets.QLabel(_("Image storage locations"))
        self.ui["locations_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["locations_list_label"])

        self.ui["locations_list"] = self.locations_list.display_widget
        self.ui["layout"].addWidget(self.ui["locations_list"])

        self.ui["methods_list_label"] = QtWidgets.QLabel(_("Conversion methods"))
        self.ui["methods_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["methods_list_label"])

        self.ui["conversion_methods_list"] = self.conversion_methods_list.display_widget
        self.ui["layout"].addWidget(self.ui["conversion_methods_list"])

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        return self.ui["main"]

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/settings.png"), self.name, self.parent_window
        )
        button.setStatusTip(self.name)
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def refresh_display(self):
        """Updates the locations names & paths displayed on screen"""

        self.locations_list.refresh_display()
        self.conversion_methods_list.refresh_display()
