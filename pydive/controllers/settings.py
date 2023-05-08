"""Settings screen: Define folders for picture storage, Subsurface file, ...

Classes
----------
SettingsController
    Settings screen: Define folders for picture storage, Subsurface file, ...
"""
import gettext

from PyQt5 import QtWidgets, QtGui

from controllers.widgets.pathselectbutton import PathSelectButton

_ = gettext.gettext


class SettingsController:
    """Settings screen: Define folders for picture storage, Subsurface file, ...

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
        Reloads the paths displayed in the UI
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

        # TODO: Allow creation of new paths

        # Paths for data
        self.ui["paths"] = {}

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        for location in self.database.storagelocations_get():
            self.ui["paths"][location.id] = {}
            folder = self.ui["paths"][location.id]
            folder["model"] = location

            # Path name
            folder["name"] = QtWidgets.QWidget()
            folder["name_layout"] = QtWidgets.QStackedLayout()

            folder["name_label"] = QtWidgets.QLabel()

            folder["name_edit"] = QtWidgets.QLineEdit()
            folder["name_edit"].returnPressed.connect(
                lambda: self.on_validate_name_change(location_id)
            )

            folder["name"].setLayout(folder["name_layout"])
            folder["name_layout"].insertWidget(0, folder["name_label"])
            folder["name_layout"].insertWidget(1, folder["name_edit"])

            # Change path name
            folder["name_change"] = QtWidgets.QWidget()
            folder["name_change_layout"] = QtWidgets.QStackedLayout()
            folder["name_change_start"] = QtWidgets.QPushButton(
                QtGui.QIcon("assets/images/modify.png"), "", self.parent_window
            )
            folder["name_change_start"].clicked.connect(
                lambda: self.on_click_name_change(location.id)
            )
            folder["name_change_end"] = QtWidgets.QPushButton(
                QtGui.QIcon("assets/images/done.png"), "", self.parent_window
            )
            folder["name_change_end"].clicked.connect(
                lambda: self.on_validate_name_change(location.id)
            )
            folder["name_change"].setLayout(folder["name_change_layout"])
            folder["name_change_layout"].insertWidget(0, folder["name_change_start"])
            folder["name_change_layout"].insertWidget(1, folder["name_change_end"])

            # Actual path
            folder["path"] = QtWidgets.QLineEdit()
            folder["path"].setEnabled(False)

            # Path change
            folder["path_change"] = PathSelectButton(_("Change"), location.type.name)
            folder["path_change"].pathSelected.connect(
                lambda a, location=location: self.set_storagelocation(location.id, a)
            )

            # Add all to UI
            self.ui["layout"].addWidget(folder["name"], len(self.ui["paths"]), 0)
            self.ui["layout"].addWidget(folder["name_change"], len(self.ui["paths"]), 1)
            self.ui["layout"].addWidget(folder["path"], len(self.ui["paths"]), 2)
            self.ui["layout"].addWidget(folder["path_change"], len(self.ui["paths"]), 3)
        self.refresh_display()
        return self.ui["main"]

    def on_click_name_change(self, location_id):
        """Displays fields to modify the location name"""
        location = self.ui["paths"][location_id]

        # Update display
        location["name_edit"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(1)
        location["name_change_layout"].setCurrentIndex(1)

    def on_validate_name_change(self, location_id):
        """Saves the storage location name"""
        location = self.ui["paths"][location_id]
        # Save the change
        location["model"].name = location["name_edit"].text()
        self.database.session.add(location["model"])
        self.database.session.commit()

        # Update display
        location["name_label"].setText(location["model"].name)

        # Make widgets visible
        location["name_layout"].setCurrentIndex(0)
        location["name_change_layout"].setCurrentIndex(0)

    def set_storagelocation(self, location_id, path):
        """Saves the storage location path"""
        location = self.ui["paths"][location_id]

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
        """Refreshes the display - update the paths displayed"""
        # Refresh list of paths
        for id, location in self.ui["paths"].items():
            location["name_label"].setText(location["model"].name)
            location["name_edit"].setText(location["model"].name)
            location["path"].setText(location["model"].path)
            location["path_change"].target = location["model"].path
