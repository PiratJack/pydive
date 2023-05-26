"""Settings screen: Define locations for picture storage, Subsurface file, ...

Classes
----------
SettingsController
    Settings screen: Define locations for picture storage, Subsurface file, ...
"""
import gettext

from PyQt5 import QtWidgets, QtGui, QtCore

from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.iconbutton import IconButton
import models.storagelocation
from models.base import ValidationException

_ = gettext.gettext


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
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()
        self.ui["layout"].setColumnStretch(0, 10)
        self.ui["layout"].setColumnStretch(1, 1)
        self.ui["layout"].setColumnStretch(2, 15)
        self.ui["layout"].setColumnStretch(3, 1)
        self.ui["layout"].setColumnStretch(4, 1)

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        self.ui["locations"] = {}
        # TODO: Display conversion methods & allow to create new ones

        self.new_location = None

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        self.ui["locations"] = {}
        for location_model in self.database.storagelocations_get():
            self.add_location_ui(location_model)

        # Create new location
        self.ui["add_new"] = IconButton(
            QtGui.QIcon("assets/images/add.png"), "", self.parent_window
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
            QtGui.QIcon("assets/images/modify.png"), "", self.parent_window
        )
        # dlocation["name_change_start"].setMinimumWidth(100)
        location["name_change_start"].clicked.connect(
            lambda: self.on_click_name_change(location["model"].id)
        )
        location["name_change_layout"].insertWidget(0, location["name_change_start"])

        # Location name - Validate button
        location["name_change_end"] = IconButton(
            QtGui.QIcon("assets/images/done.png"), "", self.parent_window
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
            _("Change"), location_model.type.name
        )
        location["path_change"].pathSelected.connect(
            lambda a, location=location: self.on_validate_path_change(
                location["model"].id, a
            )
        )
        self.ui["layout"].addWidget(
            location["path_change"], len(self.ui["locations"]), 3
        )

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
        # TODO: Allow to create locations of type "file" (for dive log)
        location["path_change"] = PathSelectButton(_("Change"), "folder")
        location["path_change"].pathSelected.connect(
            lambda a, location=location: self.on_validate_path_change(0, a)
        )
        self.ui["layout"].addWidget(
            location["path_change"], len(self.ui["locations"]), 3
        )

        # Location name - Validate button
        location["validate_new"] = IconButton(
            QtGui.QIcon("assets/images/done.png"), "", self.parent_window
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
        # TODO: Allow to create locations of type "file" (for dive log)
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

        # Refresh list of locations
        for location in self.ui["locations"].values():
            location["name_label"].setText(location["model"].name)
            location["name_edit"].setText(location["model"].name)
            location["path"].setText(location["model"].path)
            location["path_change"].target = location["model"].path
