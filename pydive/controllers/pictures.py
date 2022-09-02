"""Displays pictures, where they are stored & allows to choose which version to keep

Classes
----------
PicturesTree
    The tree displaying the pictures

PicturesController
    Picture organization, selection & link to trips
"""
import gettext

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

import models.repository
from controllers.widgets.pathselectbutton import PathSelectButton
from controllers.widgets.basetreewidget import BaseTreeWidget

_ = gettext.gettext


class PicturesTree  (BaseTreeWidget):
    """Picture organization, selection & link to trips

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
        The window displaying this controller
    repository: models.repository.Repository
        A reference to the picture repository
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

    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("SD Card"),
            "size": 0.2,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Temporary storage"),
            "size": 0.2,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Archives"),
            "size": 0.2,
            "alignment": Qt.AlignCenter,
        },
    ]

    def __init__(self, trips):
        self.trips = trips

    def fill_tree(self):
        self.clear()

        for trip, pictures in self.trips.items():
            trip_widget = self.add_trip(trip)
            for picture in pictures:
                self.add_picture(trip_widget, picture)

    def add_trip(self, trip):
        data = [trip, '', '', '']
        trip_widget = QtWidgets.QTreeWidgetItem(data)
        self.addTopLevelItem(trip_widget)

        for column, field in enumerate(self.columns):
            trip_widget.setTextAlignment(column, field["alignment"])

        return trip_widget

    def add_picture(self, trip_widget, picture):
        data = [picture, '', '', '']
        picture_widget = QtWidgets.QTreeWidgetItem(data)
        self.addTopLevelItem(trip_widget)
        ######################
        # TODO : Organize per trip AND per picture name
        ######################

        trip_widget.addChild(picture_widget)

class PicturesController:
    """Picture organization, selection & link to trips

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
        The window displaying this controller
    repository: models.repository.Repository
        A reference to the picture repository
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

    name = _("Pictures")

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements.

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        self.parent_window = parent_window
        self.repository = models.repository.Repository()

        self.ui = {}
        self.ui['main'] = QtWidgets.QWidget()
        self.ui['layout'] = QtWidgets.QHBoxLayout()

        self.ui['main'].setLayout(self.ui['layout'])

        # Left part: folders + picture locations
        self.ui['left'] = QtWidgets.QWidget()
        self.ui['left_layout'] = QtWidgets.QVBoxLayout()
        self.ui['left'].setLayout(self.ui['left_layout'])
        self.ui['layout'].addWidget(self.ui['left'], 1)

        self.ui['folders'] = {}
        for path in ['SD Card', 'Temporary storage', 'Archive']:
            self.ui['folders'][path] = PathSelectButton(path, "folder")
            self.ui['left_layout'].addWidget(self.ui['folders'][path], len(self.ui['folders']))
            #TODO: Display the correct paths (from database?) & remove the below testing
            if path == "SD Card":
                self.ui['folders'][path].target = "/home/PiratJack/Programmation/Python/PyDive/staging/SD/"
            elif path == "Temporary storage":
                self.ui['folders'][path].target = "/home/PiratJack/Programmation/Python/PyDive/staging/temporary/"
            elif path == "Archive":
                self.ui['folders'][path].target = "/home/PiratJack/Programmation/Python/PyDive/staging/archive/"


        # Right part: choose picture to keep + tasks in progress
        self.ui['right'] = QtWidgets.QWidget()
        self.ui['right_layout'] = QtWidgets.QVBoxLayout()
        self.ui['right'].setLayout(self.ui['right_layout'])
        self.ui['layout'].addWidget(self.ui['right'], 1)

        self.ui['load_button'] = QtWidgets.QPushButton(_("Load pictures"))
        self.ui['load_button'].clicked.connect(self.on_load_pictures)
        self.ui['right_layout'].addWidget(self.ui['load_button'])

        # #self.images = []
        # #for i in [0,1]:
            # #pass
            # #self.images[i] = QtWidgets.QPixmap()
            # #self.right_column.layout.addWidget(self.images[i])

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        return self.ui['main']

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/pictures.png"), _("Pictures"), self.parent_window
        )
        button.setStatusTip(_("Organize pictures"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def on_load_pictures(self):
        """User clicks 'load pictures' => reload the tree of pictures"""
        self.repository.load_pictures({name: widget.target for name, widget in self.ui['folders'].items() if widget.target})

    def refresh_display(self):
        """Refreshes the display - update trips & pictures"""
        #TODO: Implement pictures refresh
        pass
