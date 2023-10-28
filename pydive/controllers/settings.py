"""Settings screen: Define locations for picture storage, Subsurface file, ...

Classes
----------
SettingsController
    Settings screen: Define locations for picture storage, Subsurface file, ...
LocationsList
    Displays locations & allows to modify them
ConversionMethodsList
    Displays conversion methods & allows to modify them
CategoriesList
    Displays categories & allows to modify them
"""
import gettext
import logging
import os

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.iconbutton import IconButton
import models.storagelocation
import models.conversionmethod
import models.category
from models.base import ValidationException

_ = gettext.gettext
logger = logging.getLogger(__name__)


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
    __init__ (parent_controller, location_type)
        Stores reference to parent controller & defines UI elements.
    add_location_ui (location_model)
        Adds the fields for the provided location
    on_click_name_change (location_id)
        Displays fields to modify the location name
    on_validate_name_change (location_id)
        Saves the storage location name
    on_validate_path_change (location_id, path)
        Saves the storage location path
    on_click_new_location
        Displays all the fields to create a new location
    on_validate_new_location
        Saves a new location
    on_click_delete_location (location_id)
        Deletes a location
    display_error (location_id, field, message)
        Displays an error for a given location & field
    clear_error (location_id, field)
        Hides all errors of a given location & field
    delete_fields_for_location (location_id)
        Removes a location from display
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
            "name": None,  # Name change
            "stretch": 1,
        },
        {
            "name": _("Path"),
            "stretch": 15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Path change
            "stretch": 1,
        },
        {
            "name": None,  # Delete (for picture folders)
            "stretch": 1,
        },
    ]

    def __init__(self, parent_controller, location_type):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        location_type : Either "file" for dive log file or "picture_folder" for image folders
            The type of locations to display / edit
        """
        logger.debug(f"LocationsList.init {location_type}")
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget(parent_controller.ui["main"])
        self.ui["layout"] = QtWidgets.QGridLayout()
        self.location_type = models.storagelocation.StorageLocationType[location_type]

        # Add headers
        for i, col in enumerate(self.columns):
            # Note: _ is added here again because, otherwise, it doesn't translate
            header = QtWidgets.QLabel(_(col["name"]), self.ui["main"])
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
        if self.location_type.name == "picture_folder":
            locations = self.database.storagelocations_get_picture_folders()

            # Create new location
            self.ui["add_new"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/add.png"
                ),
                "",
                self.ui["main"],
            )
            self.ui["add_new"].clicked.connect(lambda: self.on_click_new_location())

            self.ui["layout"].addWidget(self.ui["add_new"], len(locations) + 1, 1)

        else:
            # Divelog ==> do not allow to create new ones
            locations = self.database.storagelocations_get_divelog()
            if not locations:
                divelog = models.storagelocation.StorageLocation()
                divelog.type = self.location_type
                divelog.name = "Dive log"
                divelog.path = " "
                self.database.session.add(divelog)
                self.database.session.commit()

                locations = [divelog]

        for location_model in locations:
            self.add_location_ui(location_model)

        self.refresh_display()
        return self.ui["main"]

    def add_location_ui(self, location_model):
        """Adds the fields for the provided location

        Parameters
        ----------
        location_model : models.storagelocation.StorageLocation
            The storage location to display
        """
        logger.info(f"LocationsList.add_location_ui {location_model}")
        self.ui["locations"][location_model.id] = {}
        row = len(self.ui["locations"])

        location = self.ui["locations"][location_model.id]
        location["model"] = location_model
        location["error"] = {}

        # Location name
        location["name_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        location["name_wrapper_layout"] = QtWidgets.QVBoxLayout()
        location["name_wrapper"].setLayout(location["name_wrapper_layout"])
        self.ui["layout"].addWidget(location["name_wrapper"], row, 0)

        location["name_stack"] = QtWidgets.QWidget(location["name_wrapper"])
        location["name_stack_layout"] = QtWidgets.QStackedLayout()
        location["name_stack"].setLayout(location["name_stack_layout"])
        location["name_wrapper_layout"].addWidget(location["name_stack"])

        # Location name - Display
        location["name_label"] = QtWidgets.QLabel(location["name_stack"])
        location["name_stack_layout"].addWidget(location["name_label"])

        # Location name - Edit box
        location["name_edit"] = QtWidgets.QLineEdit(location["name_stack"])
        location["name_edit"].returnPressed.connect(
            lambda: self.on_validate_name_change(location_model.id)
        )
        location["name_stack_layout"].addWidget(location["name_edit"])

        # Location name - Edit / validate button
        location["name_change"] = QtWidgets.QWidget(self.ui["main"])
        location["name_change"].setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        location["name_change_layout"] = QtWidgets.QStackedLayout()
        location["name_change"].setLayout(location["name_change_layout"])
        self.ui["layout"].addWidget(location["name_change"], row, 1)

        # Location name - Edit button
        location["name_change_start"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/modify.png"
            ),
            "",
            location["name_change"],
        )
        location["name_change_start"].clicked.connect(
            lambda: self.on_click_name_change(location["model"].id)
        )
        location["name_change_layout"].insertWidget(0, location["name_change_start"])

        # Location name - Validate button
        location["name_change_end"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/save.png"
            ),
            "",
            location["name_change"],
        )
        location["name_change_end"].clicked.connect(
            lambda: self.on_validate_name_change(location["model"].id)
        )
        location["name_change_layout"].insertWidget(1, location["name_change_end"])

        # Location path
        location["path_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        location["path_wrapper_layout"] = QtWidgets.QVBoxLayout()
        location["path_wrapper"].setLayout(location["path_wrapper_layout"])
        self.ui["layout"].addWidget(location["path_wrapper"], row, 2)

        location["path_edit"] = QtWidgets.QLineEdit(location["path_wrapper"])
        location["path_edit"].setEnabled(False)
        location["path_wrapper_layout"].addWidget(location["path_edit"])

        # Location path change
        location["path_change"] = PathSelectButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/modify.png"
            ),
            self.ui["main"],
            location_model.type.value["file_or_folder"],
        )
        location["path_change"].pathSelected.connect(
            lambda path, location=location: self.on_validate_path_change(
                location["model"].id, path
            )
        )
        self.ui["layout"].addWidget(location["path_change"], row, 3)

        if self.location_type.name == "picture_folder":
            # Delete location
            location["delete"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/delete.png"
                ),
                "",
                self.ui["main"],
            )
            location["delete"].clicked.connect(
                lambda a, location=location: self.on_click_delete_location(
                    location["model"].id
                )
            )
            self.ui["layout"].addWidget(location["delete"], row, 4)

    def on_click_name_change(self, location_id):
        """Displays fields to modify the location name

        Parameters
        ----------
        location_id : int
            The ID of the location whose name needs to change
        """
        logger.debug(f"LocationsList.on_click_name_change {location_id}")
        location = self.ui["locations"][location_id]

        # Update display
        location["name_edit"].setText(location["model"].name)

        # Make widgets visible
        location["name_stack_layout"].setCurrentIndex(1)
        location["name_change_layout"].setCurrentIndex(1)

    def on_validate_name_change(self, location_id):
        """Saves the storage location name

        Parameters
        ----------
        location_id : int
            The ID of the location whose name needs to change
        """
        logger.debug(f"LocationsList.on_validate_name_change {location_id}")
        location = self.ui["locations"][location_id]
        # Save the change
        try:
            location["model"].name = location["name_edit"].text()
            # For dive log: if the name is edited before the path, it should not crash
            if location["model"].path:
                self.database.session.add(location["model"])
                self.database.session.commit()
                self.clear_error(location_id, "name")
        except ValidationException as error:
            self.display_error(location["model"].id, "name", error.message)
            return

        # Update display
        location["name_label"].setText(location["model"].name)

        # Make widgets visible
        location["name_stack_layout"].setCurrentIndex(0)
        location["name_change_layout"].setCurrentIndex(0)

    def on_validate_path_change(self, location_id, path):
        """Saves the storage location path

        Parameters
        ----------
        location_id : int
            The ID of the location whose path needs to change
        """
        logger.debug(f"LocationsList.on_validate_path_change {location_id}")
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
        location["path_edit"].setText(path)

    def on_click_new_location(self):
        """Displays all the fields to create a new location"""
        logger.debug("LocationsList.on_click_new_location")
        self.delete_fields_for_location(0)

        # Create fields for new location
        self.ui["locations"][0] = {}
        row = len(self.ui["locations"])
        location = self.ui["locations"][0]
        location["error"] = {}

        # Location name
        location["name_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        location["name_wrapper_layout"] = QtWidgets.QVBoxLayout()
        location["name_wrapper"].setLayout(location["name_wrapper_layout"])
        self.ui["layout"].addWidget(location["name_wrapper"], row, 0)

        location["name_edit"] = QtWidgets.QLineEdit(location["name_wrapper"])
        location["name_wrapper_layout"].addWidget(location["name_edit"])

        # Location path
        location["path_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        location["path_wrapper_layout"] = QtWidgets.QVBoxLayout()
        location["path_wrapper"].setLayout(location["path_wrapper_layout"])
        self.ui["layout"].addWidget(location["path_wrapper"], row, 2)

        location["path_edit"] = QtWidgets.QLineEdit(location["path_wrapper"])
        location["path_edit"].setEnabled(False)
        location["path_wrapper_layout"].addWidget(location["path_edit"])

        # Location path change
        location["path_change"] = PathSelectButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/modify.png"
            ),
            self.ui["main"],
            self.location_type.value["file_or_folder"],
        )
        location["path_change"].pathSelected.connect(
            lambda a, location=location: self.on_validate_path_change(0, a)
        )
        self.ui["layout"].addWidget(location["path_change"], row, 3)

        # Location - Validate button
        location["validate_new"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/save.png"
            ),
            "",
            self.ui["main"],
        )
        location["validate_new"].clicked.connect(self.on_validate_new_location)
        self.ui["layout"].addWidget(location["validate_new"], row, 4)

        # Move the New button to another row
        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["locations"]) + 1, 1
        )

    def on_validate_new_location(self):
        """Saves a new location"""
        logger.debug("LocationsList.on_validate_new_location")
        location = self.ui["locations"][0]

        if not self.new_location:
            self.new_location = models.storagelocation.StorageLocation()

        # Clear previous errors
        for field in ["name", "path"]:
            self.clear_error(0, field)
        location["error"] = {}

        # Apply values in each field
        self.new_location.type = self.location_type
        for field in ["name", "path"]:
            try:
                setattr(self.new_location, field, location[field + "_edit"].text())
                self.clear_error(0, field)
            except ValidationException as error:
                self.display_error(0, field, error.message)

        if location["error"]:
            return

        self.database.session.add(self.new_location)
        self.database.session.commit()
        logger.info(
            f"LocationsList.on_validate_new_location New location created {self.new_location}"
        )

        # Remove all "new location" fields (error fields were removed before)
        self.delete_fields_for_location(0)

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
        logger.debug("LocationsList.on_click_delete_location")
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle("Please confirm")
        dialog.setText("Do you really want to delete this storage location?")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            location = self.ui["locations"][location_id]
            self.database.delete(location["model"])
            logger.info(
                f"LocationsList.on_click_delete_location Deleted location {location['model']}"
            )
            self.delete_fields_for_location(location_id)

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
        logger.debug(
            f"LocationsList.display_error {message} for {field} on {location_id}"
        )
        location = self.ui["locations"][location_id]
        if field in location["error"]:
            location["error"][field].setText(message)
        else:
            location["error"][field] = QtWidgets.QLabel(message)
            location["error"][field].setProperty("class", "validation_error")
            location[field + "_wrapper_layout"].addWidget(
                location["error"][field],
                1,
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
        logger.debug(f"LocationsList.clear_error for {field} on {location_id}")
        location = self.ui["locations"][location_id]
        if field in location["error"]:
            location[field + "_wrapper_layout"].removeWidget(location["error"][field])
            location["error"][field].deleteLater()
            del location["error"][field]

    def delete_fields_for_location(self, location_id):
        """Deletes all fields for a given location

        Parameters
        ----------
        location_id : int
            The ID of the location to delete (0 for new locations)
        """
        logger.debug(f"LocationsList.delete_fields_for_location for {location_id}")
        if location_id not in self.ui["locations"]:
            return
        location = self.ui["locations"][location_id]

        if "model" in location:
            del location["model"]

        for field in ["name", "path"]:
            self.clear_error(location_id, field)
        del location["error"]
        for field in location:
            if "layout" not in field:
                self.ui["layout"].removeWidget(location[field])
            location[field].deleteLater()
        del self.ui["locations"][location_id]

    def refresh_display(self):
        """Updates the locations names & paths displayed on screen"""
        logger.debug("LocationsList.refresh_display")
        # Refresh list of locations
        for location in self.ui["locations"].values():
            location["name_label"].setText(location["model"].name)
            location["name_edit"].setText(location["model"].name)
            location["path_edit"].setText(location["model"].path)
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
    on_validate_field_change (field, method_id)
        Saves the storage conversion method name
    on_click_new_method (field, method_id)
        Displays all the fields to create a new conversion method
    on_validate_new_method
        Saves a new conversion method
    on_click_delete_method (method_id)
        Deletes a given conversion method
    display_error (method_id, field, message)
        Displays an error for a given method & field
    clear_error (method_id, field)
        Hides all errors of a given method & field
    delete_fields_for_method (method_id)
        Removes a method from display
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
            "name": None,  # Name change
            "stretch": 1,
        },
        {
            "name": _("File name suffix"),
            "stretch": 2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Suffix change
            "stretch": 1,
        },
        {
            "name": _("Command to execute"),
            "stretch": 15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Command change
            "stretch": 1,
        },
        {
            "name": None,  # Delete
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
        logger.debug("ConversionMethodsList.init")
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
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/add.png"
            ),
            "",
            self.ui["main"],
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
        logger.info(f"ConversionMethodsList.add_method_ui {method_model.name}")
        self.ui["methods"][method_model.id] = {}
        method = self.ui["methods"][method_model.id]
        method["model"] = method_model
        method["error"] = {}

        row = len(self.ui["methods"])
        for column, field in enumerate(["name", "suffix", "command"]):
            # Layout for the grid cell
            method[field + "_wrapper"] = QtWidgets.QWidget(self.ui["main"])
            method[field + "_wrapper_layout"] = QtWidgets.QVBoxLayout()
            method[field + "_wrapper"].setLayout(method[field + "_wrapper_layout"])
            self.ui["layout"].addWidget(method[field + "_wrapper"], row, column * 2)

            method[field + "_stack"] = QtWidgets.QWidget(method[field + "_wrapper"])
            method[field + "_stack_layout"] = QtWidgets.QStackedLayout()
            method[field + "_stack"].setLayout(method[field + "_stack_layout"])
            method[field + "_wrapper_layout"].addWidget(method[field + "_stack"])

            # Conversion method field - Display
            method[field + "_label"] = QtWidgets.QLabel(method[field + "_stack"])
            method[field + "_stack_layout"].addWidget(method[field + "_label"])

            # Conversion method field - Edit box
            method[field + "_edit"] = QtWidgets.QLineEdit(method[field + "_stack"])
            method[field + "_edit"].returnPressed.connect(
                lambda field=field: self.on_validate_field_change(
                    field, method_model.id
                )
            )
            method[field + "_stack_layout"].addWidget(method[field + "_edit"])

            # Conversion method field - Edit / validate button
            method[field + "_change"] = QtWidgets.QWidget(self.ui["main"])
            method[field + "_change"].setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )
            method[field + "_change_layout"] = QtWidgets.QStackedLayout()
            method[field + "_change"].setLayout(method[field + "_change_layout"])
            self.ui["layout"].addWidget(method[field + "_change"], row, column * 2 + 1)

            # Conversion method field - Edit button
            method[field + "_change_start"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/modify.png"
                ),
                "",
                method[field + "_change"],
            )
            method[field + "_change_start"].clicked.connect(
                lambda a, field=field: self.on_click_field_change(
                    field, method["model"].id
                )
            )
            method[field + "_change_layout"].addWidget(method[field + "_change_start"])

            # Conversion method field - Validate button
            method[field + "_change_end"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/save.png"
                ),
                "",
                method[field + "_change"],
            )
            method[field + "_change_end"].clicked.connect(
                lambda a, field=field: self.on_validate_field_change(
                    field, method["model"].id
                )
            )
            method[field + "_change_layout"].addWidget(method[field + "_change_end"])

        # Delete Conversion method
        method["delete"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/delete.png"
            ),
            "",
            self.ui["main"],
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
        logger.debug(
            f"ConversionMethodsList.on_click_field_change {field} for {method_id}"
        )
        method = self.ui["methods"][method_id]

        # Update display
        method[field + "_edit"].setText(getattr(method["model"], field))
        if field == "command":
            # Note: _ is added here again because, otherwise, it doesn't translate
            method[field + "_edit"].setToolTip(_(self.conversion_method_help))

        # Make widgets visible
        method[field + "_stack_layout"].setCurrentIndex(1)
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
        logger.info(
            f"ConversionMethodsList.on_validate_field_change {field} for {method_id}"
        )
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
        method[field + "_stack_layout"].setCurrentIndex(0)
        method[field + "_change_layout"].setCurrentIndex(0)

    def on_click_new_method(self):
        """Displays all the fields to create a new method"""
        logger.debug("ConversionMethodsList.on_click_new_method")

        # Remove all existing fields
        self.delete_fields_for_method(0)

        # Basic structure
        self.ui["methods"][0] = {}
        method = self.ui["methods"][0]
        method["error"] = {}

        # Add all modifiable fields
        for column, field in enumerate(["name", "suffix", "command"]):
            method[field + "_wrapper"] = QtWidgets.QWidget()
            method[field + "_wrapper_layout"] = QtWidgets.QVBoxLayout()
            method[field + "_wrapper"].setLayout(method[field + "_wrapper_layout"])
            self.ui["layout"].addWidget(
                method[field + "_wrapper"], len(self.ui["methods"]), column * 2
            )

            method[field] = QtWidgets.QLineEdit()
            method[field + "_wrapper_layout"].addWidget(method[field])

        # Note: _ is added here again because, otherwise, it doesn't translate
        method["command"].setToolTip(_(self.conversion_method_help))

        # Validate button
        method["validate_new"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/save.png"
            ),
            "",
            self.ui["main"],
        )
        method["validate_new"].clicked.connect(self.on_validate_new_method)
        self.ui["layout"].addWidget(method["validate_new"], len(self.ui["methods"]), 6)

        # Move the New button to another row
        self.ui["layout"].addWidget(self.ui["add_new"], len(self.ui["methods"]) + 1, 1)

    def on_validate_new_method(self):
        """Saves a new conversion method"""
        logger.info("ConversionMethodsList.on_validate_new_method")
        method = self.ui["methods"][0]

        if not self.new_method:
            self.new_method = models.conversionmethod.ConversionMethod()

        # Clear previous errors
        for field in ["name", "suffix", "command"]:
            self.clear_error(0, field)
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
        logger.debug(
            f"ConversionMethodsList.on_validate_new_method: New method created {self.new_method}"
        )
        self.database.session.commit()

        # Remove all "new method" fields (error fields were removed before)
        self.delete_fields_for_method(0)

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
        logger.debug("ConversionMethodsList.on_click_delete_method")
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle(_("Please confirm"))
        dialog.setText(_("Do you really want to delete this conversion method?"))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            method = self.ui["methods"][method_id]
            self.database.delete(method["model"])
            logger.info(
                f"ConversionMethodsList.on_click_delete_method: Deleted {method}"
            )
            self.delete_fields_for_method(method_id)

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
        logger.debug(
            f"ConversionMethodsList.display_error: {message} for {field} on {method_id}"
        )
        method = self.ui["methods"][method_id]
        if field in method["error"]:
            method["error"][field].setText(message)
        else:
            method["error"][field] = QtWidgets.QLabel(message)
            method["error"][field].setProperty("class", "validation_error")
            method[field + "_wrapper_layout"].addWidget(method["error"][field])

    def clear_error(self, method_id, field):
        """Hides the error that was displayed for the provided field

        Parameters
        ----------
        method_id : int
            The ID of the modified method (0 for new methods)
        field : str
            The name of the field for which to clear the error
        """
        logger.debug(f"ConversionMethodsList.clear_error for {field} on {method_id}")
        method = self.ui["methods"][method_id]
        if field in method["error"]:
            method[field + "_wrapper_layout"].removeWidget(method["error"][field])
            method["error"][field].deleteLater()
            del method["error"][field]

    def delete_fields_for_method(self, method_id):
        """Deletes all fields for a given method

        Parameters
        ----------
        method_id : int
            The ID of the method to delete (0 for new methods)
        """
        logger.debug(f"MethodsList.delete_fields_for_method for {method_id}")
        if method_id not in self.ui["methods"]:
            return
        method = self.ui["methods"][method_id]

        if "model" in method:
            del method["model"]

        for field in ["name", "suffix", "command"]:
            self.clear_error(method_id, field)
        del method["error"]
        for field in method:
            if "layout" not in field:
                self.ui["layout"].removeWidget(method[field])
            method[field].deleteLater()
        del self.ui["methods"][method_id]

    def refresh_display(self):
        """Updates the methods names & paths displayed on screen"""
        logger.debug("ConversionMethodsList.refresh_display")
        # Refresh list of methods
        for method in self.ui["methods"].values():
            for field in ["name", "suffix", "command"]:
                method[field + "_label"].setText(getattr(method["model"], field))


class CategoriesList:
    """Displays categories & allows to modify them

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
    __init__ (parent_controller)
        Stores reference to parent controller & defines UI elements.
    add_category_ui (category_model)
        Adds the fields for the provided category
    on_click_text_field_change (category_id, field)
        Displays fields to modify the category name or path
    on_validate_text_field_change (category_id, field)
        Saves the category name or path
    on_validate_icon_change (category_id)
        Saves the icon based on what was selected
    on_click_new_category
        Displays all the fields to create a new category
    on_validate_new_category
        Saves a new category
    on_click_delete_category (category_id)
        Deletes a category
    display_error (category_id, field, message)
        Displays an error for a given category & field
    clear_error (category_id, field)
        Hides all errors of a given category & field
    delete_fields_for_category (category_id)
        Removes a category from display
    refresh_display
        Updates the categories names & paths displayed on screen
    """

    columns = [
        {
            "name": _("Name"),
            "stretch": 10,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Name change
            "stretch": 1,
        },
        {
            "name": _("Path"),
            "stretch": 15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Path change
            "stretch": 1,
        },
        {
            "name": _("Icon"),
            "stretch": 3,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": None,  # Delete
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
        logger.debug("CategoriesList.init")
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget(parent_controller.ui["main"])
        self.ui["layout"] = QtWidgets.QGridLayout()

        # Add headers
        for i, col in enumerate(self.columns):
            # Note: _ is added here again because, otherwise, it doesn't translate
            header = QtWidgets.QLabel(_(col["name"]), self.ui["main"])
            header.setProperty("class", "grid_header")
            if "alignment" in col:
                header.setAlignment(col["alignment"])
            self.ui["layout"].addWidget(header, 0, i)
            self.ui["layout"].setColumnStretch(i, col["stretch"])

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        self.ui["categories"] = {}
        self.new_category = None

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this list"""

        self.ui["categories"] = {}
        categories = self.database.categories_get()

        # Create new category
        self.ui["add_new"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/add.png"
            ),
            "",
            self.ui["main"],
        )
        self.ui["add_new"].clicked.connect(lambda: self.on_click_new_category())

        self.ui["layout"].addWidget(self.ui["add_new"], len(categories) + 1, 1)

        for category_model in categories:
            self.add_category_ui(category_model)

        self.refresh_display()
        return self.ui["main"]

    def add_category_ui(self, category_model):
        """Adds the fields for the provided category

        Parameters
        ----------
        category_model : models.category.Category
            The category to display
        """
        logger.info(f"CategoriesList.add_category_ui {category_model}")
        self.ui["categories"][category_model.id] = {}
        row = len(self.ui["categories"])

        category = self.ui["categories"][category_model.id]
        category["model"] = category_model
        category["error"] = {}

        for field in ["name", "relative_path"]:
            column = 0 if field == "name" else 2
            # Category name & path - stack & wrapper
            category[field + "_wrapper"] = QtWidgets.QWidget(self.ui["main"])
            category[field + "_wrapper_layout"] = QtWidgets.QVBoxLayout()
            category[field + "_wrapper"].setLayout(category[field + "_wrapper_layout"])
            self.ui["layout"].addWidget(category[field + "_wrapper"], row, column)

            category[field + "_stack"] = QtWidgets.QWidget(category[field + "_wrapper"])
            category[field + "_stack_layout"] = QtWidgets.QStackedLayout()
            category[field + "_stack"].setLayout(category[field + "_stack_layout"])
            category[field + "_wrapper_layout"].addWidget(category[field + "_stack"])

            # Category name & path - Display
            category[field + "_label"] = QtWidgets.QLabel(category[field + "_stack"])
            category[field + "_stack_layout"].addWidget(category[field + "_label"])

            # Category name & path - Edit box
            category[field + "_edit"] = QtWidgets.QLineEdit(category[field + "_stack"])
            category[field + "_edit"].returnPressed.connect(
                lambda f=field: self.on_validate_text_field_change(category_model.id, f)
            )
            category[field + "_stack_layout"].addWidget(category[field + "_edit"])

            # Category name & path - Edit / validate button
            category[field + "_change"] = QtWidgets.QWidget(self.ui["main"])
            category[field + "_change"].setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )
            category[field + "_change_layout"] = QtWidgets.QStackedLayout()
            category[field + "_change"].setLayout(category[field + "_change_layout"])
            self.ui["layout"].addWidget(category[field + "_change"], row, column + 1)

            # Category name & path - Edit button
            category[field + "_change_start"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/modify.png"
                ),
                "",
                category[field + "_change"],
            )
            category[field + "_change_start"].clicked.connect(
                lambda _a, f=field: self.on_click_text_field_change(
                    category["model"].id, f
                )
            )
            category[field + "_change_layout"].insertWidget(
                0, category[field + "_change_start"]
            )

            # Category name & path - Validate button
            category[field + "_change_end"] = IconButton(
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/save.png"
                ),
                "",
                category[field + "_change"],
            )
            category[field + "_change_end"].clicked.connect(
                lambda _a, f=field: self.on_validate_text_field_change(
                    category["model"].id, f
                )
            )
            category[field + "_change_layout"].insertWidget(
                1, category[field + "_change_end"]
            )

        # Category icon
        category["icon_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        category["icon_wrapper_layout"] = QtWidgets.QVBoxLayout()
        category["icon_wrapper"].setLayout(category["icon_wrapper_layout"])
        self.ui["layout"].addWidget(category["icon_wrapper"], row, 4)

        category["icon_change"] = PathSelectButton(
            QtGui.QIcon(category["model"].icon_path),
            self.ui["main"],
            "file",
        )
        category["icon_change"].pathSelected.connect(
            lambda icon_path, category=category: self.on_validate_icon_change(
                category["model"].id, icon_path
            )
        )
        category["icon_wrapper_layout"].addWidget(category["icon_change"])

        # Delete category
        category["delete"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/delete.png"
            ),
            "",
            self.ui["main"],
        )
        category["delete"].clicked.connect(
            lambda a, category=category: self.on_click_delete_category(
                category["model"].id
            )
        )
        self.ui["layout"].addWidget(category["delete"], row, 5)

    def on_click_text_field_change(self, category_id, field):
        """Displays fields to modify the category name or path

        Parameters
        ----------
        category_id : int
            The ID of the category whose name needs to change
        field : str
            The name of the field to change
        """
        logger.debug(f"CategoriesList.on_click_text_field_change {category_id} {field}")
        category = self.ui["categories"][category_id]

        # Update display
        category[field + "_edit"].setText(getattr(category["model"], field))

        # Make widgets visible
        category[field + "_stack_layout"].setCurrentIndex(1)
        category[field + "_change_layout"].setCurrentIndex(1)

    def on_validate_text_field_change(self, category_id, field):
        """Saves the category name or path

        Parameters
        ----------
        category_id : int
            The ID of the category whose name or path needs to change
        field : str
            The name of the field to change
        """
        logger.debug(
            f"CategoriesList.on_validate_text_field_change {category_id} {field}"
        )
        category = self.ui["categories"][category_id]
        # Save the change
        if category_id:
            try:
                setattr(category["model"], field, category[field + "_edit"].text())
                self.database.session.add(category["model"])
                self.database.session.commit()
                self.clear_error(category_id, field)
            except ValidationException as error:
                self.display_error(category["model"].id, field, error.message)
                return

        # Update display
        category[field + "_label"].setText(getattr(category["model"], field))

        # Make widgets visible
        category[field + "_stack_layout"].setCurrentIndex(0)
        category[field + "_change_layout"].setCurrentIndex(0)

    def on_validate_icon_change(self, category_id, icon):
        """Saves the category icon

        Parameters
        ----------
        category_id : int
            The ID of the category whose icon needs to change
        """
        logger.debug(f"CategoriesList.on_validate_icon_change {category_id}")
        category = self.ui["categories"][category_id]
        # Save the change for existing models
        try:
            # This is to check if the image is an actual image
            widget = QtGui.QPixmap(icon)
            if widget.isNull():
                self.display_error(
                    category_id, "icon", _("The selected icon is invalid")
                )
                return
            if category_id:
                category["model"].icon_path = icon
                self.database.session.add(category["model"])
                self.database.session.commit()
            self.clear_error(category_id, "icon_path")
        except ValidationException as error:
            self.display_error(category_id, "icon", error.message)
            return

        # Update display
        category["icon_change"].setIcon(QtGui.QIcon(icon))

    def on_click_new_category(self):
        """Displays all the fields to create a new category"""
        logger.debug("CategoriesList.on_click_new_category")
        self.delete_fields_for_category(0)

        # Create fields for new category
        self.ui["categories"][0] = {}
        row = len(self.ui["categories"])
        category = self.ui["categories"][0]
        category["error"] = {}

        for field in ["name", "relative_path"]:
            column = 0 if field == "name" else 2
            # category name
            category[field + "_wrapper"] = QtWidgets.QWidget(self.ui["main"])
            category[field + "_wrapper_layout"] = QtWidgets.QVBoxLayout()
            category[field + "_wrapper"].setLayout(category[field + "_wrapper_layout"])
            self.ui["layout"].addWidget(category[field + "_wrapper"], row, column)

            category[field + "_edit"] = QtWidgets.QLineEdit(
                category[field + "_wrapper"]
            )
            category[field + "_wrapper_layout"].addWidget(category[field + "_edit"])

        # Category icon
        category["icon_wrapper"] = QtWidgets.QWidget(self.ui["main"])
        category["icon_wrapper_layout"] = QtWidgets.QVBoxLayout()
        category["icon_wrapper"].setLayout(category["icon_wrapper_layout"])
        self.ui["layout"].addWidget(category["icon_wrapper"], row, 4)

        category["icon_change"] = PathSelectButton(
            QtGui.QIcon(),
            self.ui["main"],
            "file",
        )
        category["icon_change"].pathSelected.connect(
            lambda icon, category=category: self.on_validate_icon_change(0, icon)
        )
        category["icon_wrapper_layout"].addWidget(category["icon_change"])

        # Category - Validate button
        category["validate_new"] = IconButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/save.png"
            ),
            "",
            self.ui["main"],
        )
        category["validate_new"].clicked.connect(self.on_validate_new_category)
        self.ui["layout"].addWidget(category["validate_new"], row, 5)

        # Move the New button to another row
        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["categories"]) + 1, 1
        )

    def on_validate_new_category(self):
        """Saves a new category"""
        logger.debug("CategoriesList.on_validate_new_category")
        category = self.ui["categories"][0]

        if not self.new_category:
            self.new_category = models.category.Category()

        # Clear previous errors
        for field in ["name", "relative_path", "icon"]:
            self.clear_error(0, field)
        category["error"] = {}

        # Apply values in each field
        for field in ["name", "relative_path"]:
            try:
                setattr(self.new_category, field, category[field + "_edit"].text())
                self.clear_error(0, field)
            except ValidationException as error:
                self.display_error(0, field, error.message)
        # Apply value for icon path (slightly different usage)
        self.new_category.icon_path = category["icon_change"].target
        self.clear_error(0, "icon")

        if category["error"]:
            return

        self.database.session.add(self.new_category)
        self.database.session.commit()
        logger.info(
            f"CategoriesList.on_validate_new_category New category created {self.new_category}"
        )

        # Remove all "new category" fields (error fields were removed before)
        self.delete_fields_for_category(0)

        # Add fields for the newly created category (as "normal" fields)
        self.add_category_ui(self.new_category)
        self.refresh_display()
        self.new_category = None

        # Move the "add new" button
        self.ui["layout"].addWidget(
            self.ui["add_new"], len(self.ui["categories"]) + 1, 1
        )

    def on_click_delete_category(self, category_id):
        """Handler for delete button: deletes the category & refreshes the screen

        Parameters
        ----------
        category_id : int
            The ID of the category which should be deleted
        """
        logger.debug("CategoriesList.on_click_delete_category")
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle("Please confirm")
        dialog.setText("Do you really want to delete this category?")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            category = self.ui["categories"][category_id]
            self.database.delete(category["model"])
            logger.info(
                f"CategoriesList.on_click_delete_category Deleted category {category['model']}"
            )
            self.delete_fields_for_category(category_id)

    def display_error(self, category_id, field, message):
        """Displays an error for the provided field

        Parameters
        ----------
        category_id : int
            The ID of the modified category (0 for new categories)
        field : str
            The name of the field for which to clear the error
        message : str
            The error to display
        """
        logger.debug(
            f"CategoriesList.display_error {message} for {field} on {category_id}"
        )
        category = self.ui["categories"][category_id]
        if field in category["error"]:
            category["error"][field].setText(message)
        else:
            category["error"][field] = QtWidgets.QLabel(message)
            category["error"][field].setProperty("class", "validation_error")
            category[field + "_wrapper_layout"].addWidget(
                category["error"][field],
                1,
                QtCore.Qt.AlignBottom,
            )

    def clear_error(self, category_id, field):
        """Hides the error that was displayed for the provided field

        Parameters
        ----------
        category_id : int
            The ID of the modified category (0 for new categories)
        field : str
            The name of the field for which to clear the error
        """
        logger.debug(f"CategoriesList.clear_error for {field} on {category_id}")
        category = self.ui["categories"][category_id]
        if field in category["error"]:
            category[field + "_wrapper_layout"].removeWidget(category["error"][field])
            category["error"][field].deleteLater()
            del category["error"][field]

    def delete_fields_for_category(self, category_id):
        """Deletes all fields for a given category

        Parameters
        ----------
        category_id : int
            The ID of the category to delete (0 for new categories)
        """
        logger.debug(f"CategoriesList.delete_fields_for_category for {category_id}")
        if category_id not in self.ui["categories"]:
            return
        category = self.ui["categories"][category_id]

        if "model" in category:
            del category["model"]

        for field in ["name", "path"]:
            self.clear_error(category_id, field)
        del category["error"]
        for field in category:
            if "layout" not in field:
                self.ui["layout"].removeWidget(category[field])
            category[field].deleteLater()
        del self.ui["categories"][category_id]

    def refresh_display(self):
        """Updates the categories names & paths displayed on screen"""
        logger.debug("CategoriesList.refresh_display")
        # Refresh list of categories
        for category in self.ui["categories"].values():
            category["name_label"].setText(category["model"].name)
            category["name_edit"].setText(category["model"].name)
            category["relative_path_label"].setText(category["model"].relative_path)
            category["relative_path_edit"].setText(category["model"].relative_path)
            category["icon_change"].target = category["model"].icon_path
            category["icon_change"].setIcon(QtGui.QIcon(category["model"].icon_path))


class SettingsController:
    """Settings screen: Define locations for picture storage, Subsurface file, ...

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    code : str
        The internal name of this controller - used for references
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
    refresh_display
        Updates the display of all on-screen elements
    """

    name = _("Settings")
    code = "Settings"

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        logger.debug("SettingsController.init")
        # TODO: Reorganize display & add category management
        # Top-left: Image folders, then dive log
        # Top-right: Categories
        # Bottom, wide: Conversion methods
        #   Also update tests
        self.parent_window = parent_window
        self.database = parent_window.database
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        self.locations_list = LocationsList(self, "picture_folder")
        self.ui["locations_list_label"] = QtWidgets.QLabel(_("Image folders"))
        self.ui["locations_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["locations_list_label"])
        self.ui["locations_list"] = self.locations_list.display_widget
        self.ui["layout"].addWidget(self.ui["locations_list"])

        self.ui["layout"].addStretch()

        self.divelog_list = LocationsList(self, "file")
        self.ui["divelog_label"] = QtWidgets.QLabel(_("Dive log file"))
        self.ui["divelog_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["divelog_label"])
        self.ui["divelog"] = self.divelog_list.display_widget
        self.ui["layout"].addWidget(self.ui["divelog"])

        self.ui["layout"].addStretch()

        self.conversion_methods_list = ConversionMethodsList(self)
        self.ui["methods_list_label"] = QtWidgets.QLabel(_("Conversion methods"))
        self.ui["methods_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["methods_list_label"])
        self.ui["conversion_methods_list"] = self.conversion_methods_list.display_widget
        self.ui["layout"].addWidget(self.ui["conversion_methods_list"])

        self.ui["layout"].addStretch()

        self.categories_list = CategoriesList(self)
        self.ui["categories_list_label"] = QtWidgets.QLabel(_("Categories"))
        self.ui["categories_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["categories_list_label"])
        self.ui["categories_list"] = self.categories_list.display_widget
        self.ui["layout"].addWidget(self.ui["categories_list"])

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        self.refresh_display()
        return self.ui["main"]

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/settings.png"
            ),
            self.name,
            self.parent_window,
        )
        button.setStatusTip(self.name)
        button.triggered.connect(lambda: self.parent_window.display_tab(self.code))
        return button

    def refresh_display(self):
        """Updates the locations names & paths displayed on screen"""
        logger.debug("SettingsController.refresh_display")
        self.locations_list.refresh_display()
        self.conversion_methods_list.refresh_display()
