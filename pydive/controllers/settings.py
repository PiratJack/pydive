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

        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["layout"].setHorizontalSpacing(
            self.ui["layout"].horizontalSpacing() * 3
        )

        # TODO: Allow creation of new paths

        # Paths for data
        self.ui["paths"] = {}
        for alias in self.database.storagelocations_get():
            self.ui["paths"][alias.id] = {}
            folder = self.ui["paths"][alias.id]
            folder["button"] = PathSelectButton(alias.name, alias.type.name)
            folder["display"] = QtWidgets.QLineEdit()
            folder["model"] = alias

            self.ui["layout"].addWidget(folder["button"], len(self.ui["paths"]), 0)
            self.ui["layout"].addWidget(folder["display"], len(self.ui["paths"]), 1)

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        for alias, folder in self.ui["paths"].items():
            folder["button"].target = folder["model"].path
            folder["button"].pathSelected.connect(
                lambda a, alias=alias: self.set_storagelocation(alias, a)
            )
            folder["display"].setText(folder["model"].path)
            folder["display"].setEnabled(False)
        return self.ui["main"]

    def set_storagelocation(self, alias_id, path):
        self.ui["paths"][alias_id]["display"].setText(path)
        self.ui["paths"][alias_id]["model"].path = path
        self.database.session.add(self.ui["paths"][alias_id]["model"])
        self.database.session.commit()

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
        # TODO: Implement settings refresh

        # Refresh list of paths
        for alias, folder in self.ui["paths"].items():
            folder["button"].target = folder["model"].path
            folder["display"].setText(folder["model"].path)
