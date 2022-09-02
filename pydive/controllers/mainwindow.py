"""Main window for display. Displays a toolbar to access the different screens

Classes
----------
MainWindow
    Main window for display. Displays a toolbar to access the different screens
"""
import gettext
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize

import controllers.settings
import controllers.pictures

_ = gettext.gettext

class MainWindow(QtWidgets.QMainWindow):
    """Main window for display. Displays a toolbar to access the different screens

    Attributes
    ----------
    database : models.database.Database
        A reference to the application database
    controllers : dict of Controllers
        The different screens of the app
    layout : QtWidgets.QStackedLayout
        The main layout of the window
    toolbar : QtWidgets.QToolBar
        The toolbar displayed on the left
    """
    def __init__(self, database):
        """Stores subwindows, displays toolbar and creates the layout

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        """
        super(MainWindow, self).__init__()
        self.database = database

        self.controllers = {
            "Settings": controllers.settings.SettingsController(self),
            "Pictures": controllers.pictures.PicturesController(self),
        }

        # Define UI elements
        self.setMinimumSize(800, 600)
        self.statusBar()
        self.setWindowTitle(_("Dive management"))
        self.layout = QtWidgets.QStackedLayout()

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # Create the toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setIconSize(QSize(128, 128))

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # Add the screens to toolbar & stacked layout
        for element in self.controllers:
            self.layout.addWidget(self.controllers[element].display_widget)
            self.toolbar.addAction(self.controllers[element].toolbar_button)

        self.layout.setCurrentIndex(0)

    def display_tab(self, tab):
        """User clicks on toolbar item => display the subwindow"""
        self.layout.setCurrentIndex(list(self.controllers).index(tab))
        self.controllers[tab].refresh_display()
