"""Main window for display. Displays a toolbar to access the different screens

Classes
----------
MainWindow
    Main window for display. Displays a toolbar to access the different screens
"""
import gettext
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize

import controllers.settings
import controllers.pictures
import controllers.tasks

_ = gettext.gettext
logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    """Main window for display. Displays a toolbar to access the different screens

    Attributes
    ----------
    controllers : dict of Controllers
        The different screens of the app
    layout : QtWidgets.QStackedLayout
        The main layout of the window
    toolbar : QtWidgets.QToolBar
        The toolbar displayed on the left
    """

    def __init__(self, database, repository):
        """Stores subwindows, displays toolbar and creates the layout

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        """
        logger.debug("MainWindow.init")
        super(MainWindow, self).__init__()
        self.database = database
        self.repository = repository

        self.controllers = {
            "Settings": controllers.settings.SettingsController(self),
            "Pictures": controllers.pictures.PicturesController(self),
            "Tasks": controllers.tasks.TasksController(self),
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

        self.display_tab("Settings")

    def display_tab(self, tab):
        """User clicks on toolbar item => display the subwindow

        Parameters
        ----------
        tab : str
            The name of the tab to display"""
        logger.debug(f"MainWindow.display_tab {tab}")
        self.layout.setCurrentIndex(list(self.controllers).index(tab))
        self.controllers[tab].refresh_display()
