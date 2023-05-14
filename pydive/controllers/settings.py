"""Settings screen: Define locations for picture storage, Subsurface file, ...

Classes
----------
SettingsController
    Settings screen: Define locations for picture storage, Subsurface file, ...
"""
import gettext

from PyQt5 import QtWidgets, QtGui

from controllers.widgets.pathselectbutton import PathSelectButton

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
    on_click_name_change
        Displays fields to modify the location name
    on_validate_name_change
        Saves the storage location name
    set_storagelocation
        Saves the storage location path
    refresh_display
        Reloads the locations displayed in the UI
    """

    name = _("Settings")

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements.

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
        self.ui["layout"].setColumnStretch(0, 1)
        self.ui["layout"].setColumnStretch(2, 5)

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        # TODO: Allow creation of new locations

        self.ui["locations"] = {}

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        for location_model in self.database.storagelocations_get():
            self.ui["locations"][location_model.id] = {}
            location = self.ui["locations"][location_model.id]
            location["model"] = location_model

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
            location["name_change_start"] = QtWidgets.QPushButton(
                QtGui.QIcon("assets/images/modify.png"), "", self.parent_window
            )
            location["name_change_start"].clicked.connect(
                lambda: self.on_click_name_change(location.id)
            )
            location["name_change_layout"].insertWidget(
                0, location["name_change_start"]
            )

            # Location name - Validate button
            location["name_change_end"] = QtWidgets.QPushButton(
                QtGui.QIcon("assets/images/done.png"), "", self.parent_window
            )
            location["name_change_end"].clicked.connect(
                lambda: self.on_validate_name_change(location.id)
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
                    location_model.id, a
                )
            )
            self.ui["layout"].addWidget(
                location["path_change"], len(self.ui["locations"]), 3
            )
        self.refresh_display()
        return self.ui["main"]

    def on_click_name_change(self, location_id):
        """Displays fields to modify the location name"""
        location = self.ui["locations"][location_id]

        # Update display
        location["name_edit"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(1)
        location["name_change_layout"].setCurrentIndex(1)

    def on_validate_name_change(self, location_id):
        """Saves the storage location name"""
        location = self.ui["locations"][location_id]
        # Save the change
        location["model"].name = location["name_edit"].text()
        self.database.session.add(location["model"])
        self.database.session.commit()

        # Update display
        location["name_label"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(0)
        location["name_change_layout"].setCurrentIndex(0)

    def on_validate_path_change(self, location_id, path):
        """Saves the storage location path"""
        location = self.ui["locations"][location_id]
        location["model"].path = path

        # Save the change
        self.database.session.add(location["model"])
        self.database.session.commit()

        # Update display
        location["path"].setText(path)
        location["model"].path = path

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
        """Refreshes the display - update the locations displayed"""
        # Refresh list of locations
        for location in self.ui["locations"].values():
            location["name_label"].setText(location["model"].name)
            location["name_edit"].setText(location["model"].name)
            location["path"].setText(location["model"].path)
            location["path_change"].target = location["model"].path
