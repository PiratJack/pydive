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
from controllers.widgets.basetreewidget import BaseTreeWidget

_ = gettext.gettext


class PicturesTree(BaseTreeWidget):
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
    fill_tree
        Adds all trips & pictures to the tree
    add_trip
        Adds a single trip to the tree
    add_picture_group
        Adds a single picture group to the tree
    refresh_display
        Reloads the paths displayed in the UI
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
            "alignment": Qt.AlignLeft,
        },
    ]

    def __init__(self, parent_controller, repository):
        super().__init__(parent_controller)
        self.parent_controller = parent_controller
        self.repository = repository
        self.itemClicked.connect(self.on_item_clicked)

    def set_folders(self, folders):
        self.columns = [self.columns[0]]
        for folder in folders:
            self.columns.append(
                {
                    "name": folder.name,
                    "size": 0.2,
                    "alignment": Qt.AlignCenter,
                    "path": folder.path,
                    "model": folder,
                }
            )
        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])

    def fill_tree(self):
        """Adds all trips & pictures to the tree"""
        self.clear()
        for trip, picture_groups in self.repository.trips.items():
            trip_widget = self.add_trip(trip)
            for picture_group in picture_groups.values():
                self.add_picture_group(trip_widget, picture_group)

    def add_trip(self, trip):
        """Adds a single trip to the tree"""
        data = [trip]
        trip_widget = QtWidgets.QTreeWidgetItem(data)
        self.addTopLevelItem(trip_widget)

        for column, field in enumerate(self.columns):
            trip_widget.setTextAlignment(column, field["alignment"])

        return trip_widget

    def add_picture_group(self, trip_widget, picture_group):
        """Adds a single picture group to the tree"""
        data = [picture_group.name]
        for column in self.columns[1:]:
            data.append(str(picture_group.locations.get(column["name"], 0)))
        picture_group_widget = QtWidgets.QTreeWidgetItem(data)
        trip_widget.addChild(picture_group_widget)

    def on_item_clicked(self, item):
        # Exclude clicks on trips
        if not item.parent():
            return

        # Get selected picture group
        trip = item.parent().text(0)
        picture_group_name = item.text(0)
        picture_group = self.repository.trips[trip][picture_group_name]

        self.parent_controller.display_picture_group(picture_group)


class PictureGrid:
    def __init__(self, parent_controller):
        self.parent_controller = parent_controller
        self.pictures = {}
        self.grid = []  # Structure is row: column: widget
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()
        self.ui["main"].setProperty("class", "picture_grid")
        self.ui["main"].setLayout(self.ui["layout"])

    def display_picture_group(self, picture_group):
        # TODO: Allow to hide duplicate pictures (same name)
        # TODO: Allow to filter which pictures to display (via checkbox)
        self.clear()

        rows = [""] + list(picture_group.locations.keys())
        columns = [""] + list(picture_group.pictures.keys())

        # Add row & column headers
        self.grid.append([QtWidgets.QLabel(i) for i in columns])
        for row, location_name in enumerate(rows):
            if row == 0:  # To avoid erasing the headers on row = 0
                continue
            self.grid.append([QtWidgets.QLabel(location_name)])

        for column, conversion_type in enumerate(columns):
            for row, location_name in enumerate(rows):
                if column == 0 or row == 0:
                    self.ui["layout"].addWidget(self.grid[row][column], row, column)
                    self.grid[row][column].setProperty("class", "grid_header")
                    continue

                self.grid[row].append(PictureDisplay())

                picture = [
                    p
                    for p in picture_group.pictures[conversion_type]
                    if p.location_name == location_name
                ]
                if not picture:
                    self.grid[row][column].setImagePath()
                else:
                    # Assumption: for a given group, location and conversion type, there is a single picture
                    picture = picture[0]
                    self.grid[row][column].setImagePath(picture.path)

                self.grid[row][column].setAlignment(Qt.AlignCenter)
                self.ui["layout"].addWidget(self.grid[row][column], row, column)

    def clear(self):
        """Clears the display"""
        for row in self.grid:
            for widget in row:
                self.ui["layout"].removeWidget(widget)
                widget.deleteLater()
                widget = None
        self.grid = []

    @property
    def display_widget(self):
        return self.ui["main"]


class PictureDisplay(QtWidgets.QLabel):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap():
            ratio = self.pixmap().width() / self.pixmap().height()
            width = int(min(self.width(), self.height() * ratio))
            height = int(min(self.height(), self.width() / ratio))
            self.pixmap().swap(
                QtGui.QPixmap(self.image_path).scaled(
                    self.width(), self.height(), Qt.KeepAspectRatio
                )
            )

    def setImagePath(self, path=None):
        self.image_path = path
        if not path:
            self.setText(_("No image"))
            self.setProperty("class", "small_note")
        else:
            pixmap = QtGui.QPixmap(self.image_path)
            self.setPixmap(pixmap)
            if pixmap.width() == 0:
                del pixmap
                self.setText(_("Image not readable"))
                self.setProperty("class", "small_note")


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
    on_load_pictures
        Refreshes the tree of images (left part)
    refresh_folders
        Reloads the paths displayed at the top left
    refresh_display
        Reloads the UI
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
        self.database = parent_window.database

        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QHBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        # Left part: folders + picture locations
        self.ui["left"] = QtWidgets.QWidget()
        self.ui["left_layout"] = QtWidgets.QVBoxLayout()
        self.ui["left"].setLayout(self.ui["left_layout"])
        self.ui["layout"].addWidget(self.ui["left"], 3)
        self.ui["left"].setMinimumWidth(350)

        # Grid for the folders
        self.ui["left_grid"] = QtWidgets.QWidget()
        self.ui["left_grid_layout"] = QtWidgets.QGridLayout()
        self.ui["left_grid"].setLayout(self.ui["left_grid_layout"])
        self.ui["left_layout"].addWidget(self.ui["left_grid"])

        self.ui["folders"] = {}

        # Load button
        self.ui["load_button"] = QtWidgets.QPushButton(_("Load pictures"))
        self.ui["left_layout"].addWidget(self.ui["load_button"])

        # Picture tree
        self.ui["picture_tree"] = PicturesTree(self, self.repository)
        self.ui["left_layout"].addWidget(self.ui["picture_tree"], 1)

        # Right part: choose picture to keep + tasks in progress
        self.ui["right"] = QtWidgets.QWidget()
        self.ui["right_layout"] = QtWidgets.QVBoxLayout()
        self.ui["right"].setLayout(self.ui["right_layout"])
        self.ui["layout"].addWidget(self.ui["right"], 5)

        self.ui["pictures"] = PictureGrid(self)
        self.ui["right_layout"].addWidget(self.ui["pictures"].display_widget)

        # TODO: Allow to delete images
        # TODO: Allow to transfer images between folders
        # TODO: display loading status for background tasks

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        self.ui["load_button"].clicked.connect(self.on_load_pictures)

        return self.ui["main"]

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
        self.repository.load_pictures(
            {folder.name: folder.path for folder in self.folders}
        )

        self.ui["picture_tree"].fill_tree()

    def refresh_folders(self):
        """Refreshes the list of folders from DB"""
        # Load list from DB
        self.folders = self.database.storagelocations_get_folders()

        # Remove existing widgets
        for folder in self.ui["folders"].values():
            self.ui["left_grid_layout"].removeWidget(folder["label"])
            self.ui["left_grid_layout"].removeWidget(folder["path"])
            folder["label"].deleteLater()
            folder["path"].deleteLater()

            folder["label"] = None
            folder["path"] = None
            folder["model"] = None

        # Generate new widgets
        self.ui["folders"] = {}
        for alias in self.folders:
            self.ui["folders"][alias.id] = {}
            folder = self.ui["folders"][alias.id]
            folder["model"] = alias
            folder["label"] = QtWidgets.QLabel()
            folder["label"].setText(folder["model"].name)
            folder["path"] = QtWidgets.QLineEdit()
            folder["path"].setText(folder["model"].path)
            folder["path"].setEnabled(False)

            self.ui["left_grid_layout"].addWidget(
                folder["label"], len(self.ui["folders"]) - 1, 0
            )
            self.ui["left_grid_layout"].addWidget(
                folder["path"], len(self.ui["folders"]) - 1, 1
            )

    def refresh_display(self):
        """Refreshes the display - update trips & pictures"""
        # Refresh folder names
        self.refresh_folders()

        # Refresh image tree
        self.ui["picture_tree"].set_folders(self.folders)
        self.ui["picture_tree"].fill_tree()

    def display_picture_group(self, picture_group):
        """Displays pictures from a given group"""
        self.ui["pictures"].display_picture_group(picture_group)
