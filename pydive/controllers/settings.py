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
        self.ui = {}
        self.ui['main'] = QtWidgets.QWidget()
        self.ui['layout'] = QtWidgets.QGridLayout()

        self.ui['main'].setLayout(self.ui['layout'])
        self.ui['layout'].setHorizontalSpacing(self.ui['layout'].horizontalSpacing() * 3)

        self.ui['folders'] = {}
        self.ui['files'] = {}
        for path in ['SD Card', 'Temporary storage', 'Archive']:
            self.ui['folders'][path] = PathSelectButton(path, "folder")
            self.ui['layout'].addWidget(self.ui['folders'][path], len(self.ui['folders']), 0)
        for path in ['Subsurface dive log']:
            self.ui['files'][path] = PathSelectButton(path, "file")
            self.ui['layout'].addWidget(self.ui['files'][path], len(self.ui['folders'])+len(self.ui['files']), 0)

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        return self.ui['main']

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
        #TODO: Implement settings refresh
        pass
