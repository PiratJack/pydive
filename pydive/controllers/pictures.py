"""Displays pictures, where they are stored & allows to choose which version to keep

Classes
----------
PicturesTree
    The tree displaying the pictures

PicturesController
    Picture organization, selection & link to trips
"""
import gettext
import os
import shutil

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

import models.repository
from controllers.widgets.basetreewidget import BaseTreeWidget

_ = gettext.gettext


class PicturesTree(BaseTreeWidget):
    """Picture organization, selection & link to trips

    Attributes
    ----------
    columns : dict
        The columns to display in the tree
    parent_controller : PicturesController
        A reference to the parent controller
    repository: models.repository.Repository
        This program's picture repository

    Methods
    -------
    __init__ (parent_controller, repository)
        Stores reference to parent controller & repository + sets up event handlers
    set_folders (folders)
        Defines which folders to display
    fill_tree
        Adds all trips & pictures to the tree
    add_trip (trip)
        Adds a single trip to the tree
    add_picture_group (trip_widget, picture_group)
        Adds a single picture group to the tree
    on_item_clicked (item)
        Item clicked ==> display corresponding images
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
            "alignment": Qt.AlignLeft,
        },
    ]

    def __init__(self, parent_controller, repository):
        """Stores reference to parent controller & repository + sets up event handlers

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller
        repository : models.repository.Repository
            A reference to the picture repository
        """

        super().__init__(parent_controller)
        self.parent_controller = parent_controller
        self.repository = repository
        self.itemClicked.connect(self.on_item_clicked)

    def set_folders(self, folders):
        """Defines which folders to display

        Parameters
        ----------
        folders : list of models.storagelocations.StorageLocations
            The list of folders to display as columns in the tree
        """
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
        """Adds a single trip to the tree

        Parameters
        ----------
        trip : str
            Name of the trip
        """
        data = [trip]
        trip_widget = QtWidgets.QTreeWidgetItem(data)
        self.addTopLevelItem(trip_widget)

        for column, field in enumerate(self.columns):
            trip_widget.setTextAlignment(column, field["alignment"])

        # TODO: Trip > Right click actions:
        #  Copy everything from location A to location B
        #  Copy from A to B: submenu "all images", "only raw images", "only DT images", ...
        #  Convert images using all known methods
        #  Convert images to...: submenu "DT", "RT", ...
        #  Convert images ...: Opens a dialog:
        #    Source locations: checkboxes for each location
        #    Target : conversion method
        #    Upon confirmation, will convert all images in selected locations using selected methods

        # TODO: Trip > Right click > Change trip name
        #  Should move the corresponding folders
        return trip_widget

    def add_picture_group(self, trip_widget, picture_group):
        """Adds a single picture group to the tree

        Parameters
        ----------
        trip_widget : QtWidgets.QTreeWidgetItem
            The widget in which to add the picture group
        picture_group : models.picturegroup.PictureGroup
            The picture group to add to the tree
        """
        data = [picture_group.name]
        for column in self.columns[1:]:
            data.append(str(len(picture_group.locations.get(column["name"], []))))

        picture_group_widget = QtWidgets.QTreeWidgetItem(data)
        for col, column in enumerate(self.columns[1:]):
            pictures = picture_group.locations.get(column["name"], [])
            if pictures:
                picture_group_widget.setToolTip(
                    col + 1, "\n".join([p.filename for p in pictures])
                )
        trip_widget.addChild(picture_group_widget)
        # TODO: Image group > Right click > First part is similar as for trips
        # TODO: Image group > Right click > Add to trip:
        #  Moves the image in the right folder
        #  Updates the image's trip + moves it to the right picture_group
        #  Refresh the tree (ideally only what changed, but most likely this won't be possible

    def on_item_clicked(self, item):
        """Item clicked ==> display corresponding images

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
            The item that was clicked"""
        # Exclude clicks on trips
        if not item.parent():
            return

        # Get selected picture group
        trip = item.parent().text(0)
        picture_group_name = item.text(0)
        picture_group = self.repository.trips[trip][picture_group_name]

        self.parent_controller.display_picture_group(picture_group)


class PictureGrid:
    """Displays all pictures of a given group in a grid format

    Attributes
    ----------
    parent_controller : PicturesController
        A reference to the parent controller
    database : models.database.Database
        This program's database
    repository: models.repository.Repository
        This program's picture repository
    picture_group : models.picturegroup.PictureGroup
        The group of pictures to display
    grid : dict of dict of QtWidgets.QLabel or QtWidgets.QWidget
        The different headers & images to display
    picture_containers : dict of dict of PictureContainer
        The container for picture display
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this screen

    Methods
    -------
    __init__ (parent_controller)
        Stores reference to parent controller + initializes the display
    display_picture_group (picture_group)
        Displays the provided picture group in the grid
    clear_display
        Removes all widgets from the display & deletes them properly
    generate_image (row, column)
        Generates an image for the provided row & column
    copy_image (row, column)
        Copies an image to the provided row & column
    """

    def __init__(self, parent_controller):
        """Stores reference to parent controller + initializes the display

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller"""
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.repository = parent_controller.repository
        self.picture_group = None
        self.grid = []  # Structure is row: column: widget
        self.picture_containers = {}  # Structure is row: column: PictureContainer
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()
        self.ui["main"].setProperty("class", "picture_grid")
        self.ui["main"].setLayout(self.ui["layout"])

    def display_picture_group(self, picture_group):
        """Displays the provided picture group in the grid

        Also fills in self.grid and self.picture_containers

        Parameters
        ----------
        picture_group : models.picturegroup.PictureGroup
            The group of pictures to display"""
        # TODO: Picture grid > Allow to filter which pictures to display (via checkbox)
        self.clear_display()
        self.picture_group = picture_group

        # Include locations for existing pictures
        rows = list(picture_group.locations.keys())
        # Add all locations from DB
        rows = rows + [l.name for l in self.database.storagelocations_get_folders()]
        # "" is added for header column
        rows = [""] + sorted(set(rows))

        # Include conversion types for existing pictures
        # "" is added for RAW files
        columns = [""] + list(picture_group.pictures.keys())
        # Add conversion types based on conversion methods
        columns = columns + [m.suffix for m in self.database.conversionmethods_get()]
        # "" is added for header row
        columns = [""] + sorted(set(columns))

        # Add row & column headers
        self.grid.append([])
        for i in columns:
            try:
                label = self.database.conversionmethods_get_by_suffix(i).name
            except:
                label = i
            self.grid[0].append(QtWidgets.QLabel(label))

        for row, location_name in enumerate(rows):
            if row == 0:  # To avoid erasing the headers on row = 0
                continue
            self.grid.append([QtWidgets.QLabel(location_name)])

        # Add the images themselves
        for column, conversion_type in enumerate(columns):
            for row, location_name in enumerate(rows):
                if column == 0 or row == 0:
                    self.ui["layout"].addWidget(self.grid[row][column], row, column)
                    self.grid[row][column].setProperty("class", "grid_header")
                    continue

                picture_container = PictureContainer(self, row, column)

                # No picture at all for this conversion type
                if conversion_type not in picture_group.pictures:
                    picture_container.set_empty_picture()
                else:
                    picture = [
                        p
                        for p in picture_group.pictures[conversion_type]
                        if p.location_name == location_name
                    ]
                    if not picture:
                        picture_container.set_empty_picture()
                    else:
                        # Assumption: for a given group, location and conversion type, there is a single picture
                        picture = picture[0]
                        picture_container.set_picture(picture)

                if row not in self.picture_containers:
                    self.picture_containers[row] = {}
                self.picture_containers[row][column] = picture_container

                self.grid[row].append(picture_container.display_widget)
                self.ui["layout"].addWidget(self.grid[row][column], row, column)

    def clear_display(self):
        """Removes all widgets from the display & deletes them properly"""
        for row in self.grid:
            for element in row:
                if type(element) == PictureContainer:
                    self.ui["layout"].removeWidget(element.display_widget)
                    element.display_widget.deleteLater()
                    element.display_widget = None
                    del element
                else:
                    self.ui["layout"].removeWidget(element)
                    element.deleteLater()
                    element = None
        self.grid = []
        self.picture_group = None

    def generate_image(self, row, column):
        """Generates an image for the provided row & column

        Parameters
        ----------
        row : int
            The row in which to generate the image
        column : int
            The column in which to generate the image"""

        parameters = {
            "command": "",
            "source_file": "",
            "target_folder": "",
            "target_file": "",
        }

        # Find raw source image
        if not "" in self.picture_group.pictures:
            self.picture_containers[row][column].display_error(
                _("No source image available for generation")
            )
            return
        source = self.picture_group.pictures[""]

        # Identify the target folder
        target_location_name = self.grid[row][0].text()
        target_location = self.database.storagelocation_get_by_name(
            target_location_name
        )
        parameters["target_folder"] = target_location.path

        # Identify the source picture
        # Ideally, it should be in the target location
        source_picture = [p for p in source if p.location_name == target_location_name]
        if source_picture:
            source_picture = source_picture[0]
        else:
            source_picture = source[0]
        parameters["source_file"] = source_picture.path

        # Identify which method to use for conversion
        target_suffix = self.grid[0][column].text()
        try:
            conversion = self.database.conversionmethods_get_by_name(target_suffix)
        except:
            self.picture_containers[row][column].display_error(
                _("No conversion method found")
            )
            return
        parameters["command"] = conversion.command

        target_file_name = self.picture_group.name + "_" + conversion.suffix + ".jpg"
        target_file = os.path.join(parameters["target_folder"], target_file_name)
        parameters["target_file"] = target_file

        # Let's mix all that together!
        command = parameters["command"]
        command = command.replace("%SOURCE_FILE%", parameters["source_file"])
        command = command.replace("%TARGET_FILE%", parameters["target_file"])
        command = command.replace("%TARGET_FOLDER%", parameters["target_folder"])

        # TODO: Generate image > Put that in QProcess & process asynchronously
        os.system(command)

        # Add our new picture to the repository (& the picture group)
        self.repository.add_picture(self.picture_group, target_location, target_file)
        self.display_picture_group(self.picture_group)

    def copy_image(self, row, column):
        """Copies an image to the provided row & column

        Parameters
        ----------
        row : int
            The row in which to copy the image
        column : int
            The column in which to copy the image"""
        # Find other images in the same column
        source_picture = None
        for i in self.picture_containers.values():
            if i[column].picture:
                source_picture = i[column].picture
                break
        if not source_picture:
            self.picture_containers[row][column].display_error(
                _("No source image found")
            )
            return

        # Identify the target folder
        target_location_name = self.grid[row][0].text()
        target_location = self.database.storagelocation_get_by_name(
            target_location_name
        )

        target_path = os.path.join(
            target_location.path,
            self.picture_group.trip,
            os.path.basename(source_picture.path),
        )

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # TODO: Copy image > Put that in QProcess & process asynchronously
        shutil.copy2(source_picture.path, target_path)

        # Add our new picture to the repository (& the picture group)
        self.repository.add_picture(self.picture_group, target_location, target_path)
        self.display_picture_group(self.picture_group)

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        return self.ui["main"]


class PictureContainer:
    """Displays a single image as well as the related action buttons

    Attributes
    ----------
    parent_controller : PicturesController
        A reference to the parent controller
    row : int
        The row where the picture should be displayed
    column: int
        The row where the picture should be displayed
    picture : models.picture.Picture
        The picture to display
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this screen

    Methods
    -------
    __init__ (parent_controller, row, column)
        Stores reference to parent controller + initializes the display
    set_empty_picture
        Defines which folders to display
    set_picture (picture)
        Adds all trips & pictures to the tree
    on_click_generate
        Handler for generate button: triggers parent's handler
    on_click_copy
        Handler for copy button: triggers parent's handler
    on_click_delete
        Handler for delete button: deletes the image & refreshes the screen
    display_error (message)
        Displays the provided error message
    clear_display
        Removes all widgets from the display & deletes them properly
    """

    def __init__(self, parent_controller, row, column):
        """Stores reference to parent controller + initializes the display

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller
        row : int
            The row where the picture should be displayed
        column: int
            The row where the picture should be displayed"""
        self.parent_controller = parent_controller
        self.row = row
        self.column = column
        self.picture = None
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])
        self.ui["elements"] = {}

    def set_empty_picture(self):
        """Displays an empty image as well as action buttons"""
        self.clear_display()
        self.picture = None

        self.ui["elements"]["label"] = QtWidgets.QLabel(_("No image"))
        self.ui["elements"]["label"].setProperty("class", "small_note")
        self.ui["layout"].addWidget(self.ui["elements"]["label"])

        # Generate image from RAW file
        self.ui["elements"]["generate"] = QtWidgets.QPushButton(_("Generate"))
        # I have no idea why I had to use a lambda here, but it works...
        self.ui["elements"]["generate"].clicked.connect(
            lambda: self.on_click_generate()
        )
        self.ui["layout"].addWidget(self.ui["elements"]["generate"])

        # Copy image from another location
        self.ui["elements"]["copy"] = QtWidgets.QPushButton(_("Copy image here"))
        self.ui["elements"]["copy"].clicked.connect(self.on_click_copy)
        self.ui["layout"].addWidget(self.ui["elements"]["copy"])

    def set_picture(self, picture):
        """Displays the provided picture as well as action buttons

        Parameters
        ----------
        picture : models.picture.Picture
            The picture to display
        """
        self.clear_display()
        self.picture = picture

        # Clean existing elements
        for i in ["filename", "label", "generate", "image", "delete"]:
            if i in self.ui["elements"]:
                self.ui["elements"][i].deleteLater()
                self.ui["layout"].removeWidget(self.ui["elements"][i])
                del self.ui["elements"][i]

        self.ui["elements"]["filename"] = QtWidgets.QLabel(self.picture.filename)
        self.ui["layout"].addWidget(self.ui["elements"]["filename"])

        pixmap = QtGui.QPixmap(self.picture.path)
        # Image exists and can be read by PyQt5
        if pixmap.width() > 0:
            self.ui["elements"]["image"] = PictureDisplay()
            self.ui["elements"]["image"].image_path = self.picture.path
            self.ui["elements"]["image"].setPixmap(pixmap)
            self.ui["layout"].addWidget(self.ui["elements"]["image"])

            # Delete button
            # TODO: Ensure delete button is next to image (by default the image takes all the vertical space)
            self.ui["elements"]["delete"] = QtWidgets.QPushButton(
                QtGui.QIcon("assets/images/delete.png"), ""
            )
            self.ui["elements"]["delete"].clicked.connect(
                lambda: self.on_click_delete()
            )
            self.ui["layout"].addWidget(self.ui["elements"]["delete"])
        else:
            self.ui["elements"]["label"] = QtWidgets.QLabel(_("Image unreadable"))
            self.ui["elements"]["label"].setProperty("class", "small_note")
            self.ui["layout"].addWidget(self.ui["elements"]["label"])
            # TODO: Image unreadable > Add generate + copy buttons

    def on_click_generate(self):
        """Handler for generate button: triggers parent's handler"""
        self.parent_controller.generate_image(self.row, self.column)

    def on_click_copy(self):
        """Handler for copy button: triggers parent's handler"""
        self.parent_controller.copy_image(self.row, self.column)

    def on_click_delete(self):
        """Handler for delete button: deletes the image & refreshes the screen"""
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle("Please confirm")
        dialog.setText("Do you really want to delete this image?")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            os.unlink(self.picture.path)
            self.set_empty_picture()

    def display_error(self, message):
        """Displays the provided error message

        Parameters
        ----------
        message : str
            The message to display
        """
        if "error" not in self.ui["elements"]:
            self.ui["elements"]["error"] = QtWidgets.QLabel(message)
            self.ui["elements"]["error"].setProperty("class", "validation_warning")
            self.ui["layout"].addWidget(self.ui["elements"]["error"])
        self.ui["elements"]["error"].setText(message)

    def clear_display(self):
        """Removes all widgets from the display & deletes them properly"""
        for i in self.ui["elements"]:
            self.ui["elements"][i].deleteLater()
            self.ui["layout"].removeWidget(self.ui["elements"][i])
        self.ui["elements"] = {}

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        return self.ui["main"]


class PictureDisplay(QtWidgets.QLabel):
    """Displays a single image while preserving aspect ratio when resizing

    Methods
    -------
    resizeEvent (event)
        Overloaded method to keep aspect ratio on images
    """

    def resizeEvent(self, event):
        """Overloaded method to keep aspect ratio on images

        Parameters
        ----------
        event : QResizeEvent
            The resize event
        """
        super().resizeEvent(event)
        if self.pixmap() and self.pixmap().height():
            self.pixmap().swap(
                QtGui.QPixmap(self.image_path).scaled(
                    self.width(), self.height(), Qt.KeepAspectRatio
                )
            )


class PicturesController:
    """Picture organization, selection & link to trips

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
        The window displaying this controller
    database : models.database.Database
        This program's database
    repository: models.repository.Repository
        This program's picture repository
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
    display_picture_group
        Displays a given picture group
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

        # TODO: Pictures screen > display loading status for background tasks

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
