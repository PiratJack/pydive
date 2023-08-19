"""Displays pictures, where they are stored & allows to choose which version to keep

Classes
----------
PicturesTree
    The tree displaying the pictures
PictureGrid
    Displays all pictures of a given group in a grid format
PictureContainer
    Displays a single image as well as the related action buttons
PictureDisplay
    Displays a single image while preserving aspect ratio when resizing
PicturesController
    Picture organization, selection & link to trips
"""
import gettext
import logging

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.basetreewidget import BaseTreeWidget
from controllers.widgets.iconbutton import IconButton

_ = gettext.gettext
logger = logging.getLogger(__name__)


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
    contextMenuEvent (event)
        Displays the right-click menu for trips & picture groups
    generate_context_menu (tree_item)
        Generates the right-click menu for trips & picture groups
    add_trip_action (menu, label, type, source, target, trip, methods)
        Right-click menu: adds copy/generate/change trip name to trips
    change_trip_name (source_trip, target_trip)
        Changes the trip name of a given trip
    add_picture_group_action (menu, label, type, source, target, picture_group, methods)
        Right-click menu: adds copy/generate/change trip to picture groups
    change_picture_group_trip (picture_group_name, source_trip, target_trip)
        Changes the trip of a given picture group
    set_folders (folders)
        Defines which folders to display
    fill_tree
        Adds all trips & pictures to the tree
    add_trip (trip)
        Adds a single trip to the tree
    add_picture_group (trip_widget, picture_group, picture_group_widget)
        Adds a single picture group to the tree
    remove_picture_group (picture_group_widget)
        Removes a picture group from display
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
        logger.debug("PicturesTree.init")
        super().__init__(parent_controller)
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.repository = repository
        self.itemClicked.connect(self.on_item_clicked)

    def contextMenuEvent(self, event):
        """Right-click menu: copy & generate pictures

        Parameters
        ----------
        event : QContextMenuEvent
            A reference to the right-click event
        """

        index = self.indexAt(event.pos())

        if not index.isValid():
            return

        tree_item = self.itemFromIndex(index)

        self.generate_context_menu(tree_item)

        self.menu.exec_(event.globalPos())

    def generate_context_menu(self, tree_item):
        self.menu = QtWidgets.QMenu()
        self.menu_actions = []
        self.submenus = []
        # This only stores references, otherwise the menu disappears immediately
        locations = self.database.storagelocations_get_folders()
        methods = self.database.conversionmethods_get()
        # No parent = trip
        if not tree_item.parent():
            trip = tree_item.text(0)
            # Copy images
            for source in locations:
                for target in locations:
                    if source == target:
                        continue
                    label = _("Copy all images from {source} to {target}").format(
                        source=source.name, target=target.name
                    )
                    self.add_trip_action(self.menu, label, "copy", source, target, trip)

            self.menu.addSeparator()

            # Convert / Generate images
            for location in locations:
                label = _("Convert images in {location}").format(location=location.name)
                submenu = QtWidgets.QMenu(label, self.menu)
                self.menu.addMenu(submenu)

                sublabel = _("Using all methods")
                full_label = _("Convert images in {location} using all methods").format(
                    location=location.name
                )
                self.add_trip_action(
                    submenu,
                    sublabel,
                    "generate",
                    location,
                    location,
                    trip,
                    methods,
                    full_label,
                )

                for method in methods:
                    sublabel = _("Using {method}").format(method=method.name)
                    full_label = _(
                        "Convert images in {location} using method {method}"
                    ).format(location=location.name, method=method.name)
                    self.add_trip_action(
                        submenu,
                        sublabel,
                        "generate",
                        location,
                        location,
                        trip,
                        [method],
                        full_label,
                    )

                self.submenus.append(submenu)

            self.menu.addSeparator()

            # Change trip action
            label = _("Change name to ...")
            self.add_trip_action(
                self.menu,
                label,
                "change_trip",
                location,
                location,
                trip,
            )

        # Picture groups
        else:
            trip = tree_item.parent().text(0)
            picture_group_name = tree_item.text(0)
            picture_group = self.repository.trips[trip][picture_group_name]

            # Copy actions
            for source in locations:
                for target in locations:
                    if source == target:
                        continue
                    label = _("Copy all images from {source} to {target}").format(
                        source=source.name, target=target.name
                    )
                    self.add_picture_group_action(
                        self.menu, label, "copy", source, target, picture_group
                    )

            self.menu.addSeparator()

            # Conversion / generation actions
            for location in locations:
                label = _("Convert images in {location}").format(location=location.name)
                submenu = QtWidgets.QMenu(label, self.menu)
                self.menu.addMenu(submenu)

                sublabel = _("Using all methods")
                full_label = _("Convert images in {location} using all methods").format(
                    location=location.name
                )
                self.add_picture_group_action(
                    submenu,
                    sublabel,
                    "generate",
                    location,
                    location,
                    picture_group,
                    methods,
                    full_label,
                )

                for method in methods:
                    sublabel = _("Using {method}").format(method=method.name)
                    full_label = _(
                        "Convert images in {location} using method {method}"
                    ).format(location=location.name, method=method.name)
                    self.add_picture_group_action(
                        submenu,
                        sublabel,
                        "generate",
                        location,
                        location,
                        picture_group,
                        [method],
                        full_label,
                    )

                self.submenus.append(submenu)

            self.menu.addSeparator()

            # Change trip action
            label = _("Change trip to ...")
            self.add_picture_group_action(
                self.menu,
                label,
                "change_trip",
                location,
                location,
                picture_group,
                methods,
            )

    def add_trip_action(
        self, menu, label, type, source, target, trip, methods=None, full_label=None
    ):
        """Right-click menu: adds copy/generate/change trip name to trips

        Parameters
        ----------
        menu : QMenu
            The overall context menu
        label : str
            The name of the action
        type : str ('copy', 'generate' or 'change_trip')
            Which action to perform when the user clicks
        source : StorageLocation
            The source of the copy or generation (source=target for generation)
        target : StorageLocation
            The target of the copy or generation (source=target for generation)
        trip : str
            The name of the trip
        methods : list of ConversionMethods
            Which conversion method to use when the user clicks (None uses all methods)
        """
        if not full_label:
            full_label = label
        action = QtWidgets.QAction(label)
        if type == "copy":
            action.triggered.connect(
                lambda: self.repository.copy_pictures(
                    full_label, target, trip=trip, source_location=source
                )
            )
        elif type == "generate":
            action.triggered.connect(
                lambda: self.repository.generate_pictures(
                    full_label, target, methods, trip=trip, source_location=source
                )
            )
        elif type == "change_trip":

            def open_dialog(parent_controller):
                target_trip, confirmed = QtWidgets.QInputDialog.getText(
                    parent_controller.parent_window,
                    _("Rename trip"),
                    _("Trip name:"),
                    QtWidgets.QLineEdit.Normal,
                    trip,
                )
                if confirmed:
                    process_group = self.repository.change_trip_pictures(
                        full_label + target_trip,
                        target_trip,
                        trip,
                    )
                    process_group.finished.connect(
                        lambda: self.change_trip_name(trip, target_trip)
                    )

            action.triggered.connect(lambda: open_dialog(self.parent_controller))
        else:
            raise ValueError("Action must be copy, generate or change_trip")

        menu.addAction(action)
        self.menu_actions.append(action)

    def change_trip_name(self, source_trip, target_trip):
        """Changes the trip name of a given trip

        Merges trips if needed

        Parameters
        ----------
        source_trip : str
            The name of the trip to rename
        target_trip : str
            The target name of the trip
        """
        logger.info(f"PicturesTree.change_trip_name: {source_trip} to {target_trip}")
        # Source trip widget will be deleted thanks to remove_picture_group
        # We simply need to add a new one if needed, and to connect the picture groups to it

        # Does the target trip already exist in the tree?
        widgets = self.findItems(target_trip, Qt.MatchExactly, 0)
        widgets = [w for w in widgets if not w.parent()]
        if len(widgets) == 0:
            target_trip_widget = self.add_trip(target_trip)
        else:
            # There should be at most 1 match
            target_trip_widget = widgets[0]

        # Need to refresh the repository, otherwise it'll be missing pictures
        self.repository.load_pictures()
        picture_groups = self.repository.trips[target_trip].values()
        logger.debug(
            f"PicturesTree.change_trip_name: processing {len(picture_groups)} groups"
        )
        # Remove any existing children
        target_trip_widget.takeChildren()
        for picture_group in picture_groups:
            self.add_picture_group(target_trip_widget, picture_group)

    def add_picture_group_action(
        self,
        menu,
        label,
        type,
        source,
        target,
        picture_group,
        methods=None,
        full_label=None,
    ):
        """Right-click menu: adds copy/generate/change trip to picture groups

        Parameters
        ----------
        menu : QMenu
            The overall context menu
        label : str
            The name of the action
        type : str ('copy', 'generate' or 'change_trip')
            Which action to perform when the user clicks
        source : StorageLocation
            The source of the copy or generation (source=target for generation)
        target : StorageLocation
            The target of the copy or generation (source=target for generation)
        picture_group : PictureGroup
            The picture group to copy or generate
        methods : list of ConversionMethods
            Which conversion method to use when the user clicks (None uses all methods)
        """
        if not full_label:
            full_label = label
        action = QtWidgets.QAction(label)
        if type == "copy":
            action.triggered.connect(
                lambda: self.repository.copy_pictures(
                    full_label,
                    target,
                    picture_group=picture_group,
                    source_location=source,
                )
            )
        elif type == "generate":
            action.triggered.connect(
                lambda: self.repository.generate_pictures(
                    full_label,
                    target,
                    methods,
                    picture_group=picture_group,
                    source_location=source,
                )
            )
        elif type == "change_trip":

            def open_dialog(parent_controller):
                target_trip, confirmed = QtWidgets.QInputDialog.getText(
                    parent_controller.parent_window,
                    _("Rename trip"),
                    _("Trip name:"),
                    QtWidgets.QLineEdit.Normal,
                    picture_group.trip,
                )
                if confirmed:
                    source_trip = picture_group.trip
                    process_group = self.repository.change_trip_pictures(
                        full_label,
                        target_trip,
                        picture_group.trip,
                        picture_group,
                    )
                    process_group.finished.connect(
                        lambda: self.change_picture_group_trip(
                            picture_group.name, source_trip, target_trip
                        )
                    )

            action.triggered.connect(lambda: open_dialog(self.parent_controller))
        else:
            raise ValueError("Action must be copy, generate or change_trip")

        menu.addAction(action)
        self.menu_actions.append(action)

    def change_picture_group_trip(self, picture_group_name, source_trip, target_trip):
        """Changes the trip of a given picture group

        Parameters
        ----------
        picture_group_name : str
            The name of the picture group
        source_trip : str
            The trip in which the picture group is prior to the move
        target_trip : str
            The trip in which to move the picture group
        """
        logger.info(
            f"PicturesTree.change_picture_group_trip: {source_trip} to {target_trip} for {picture_group_name}"
        )
        # Does the target already exist in the tree?
        widgets = self.findItems(target_trip, Qt.MatchExactly, 0)
        widgets = [w for w in widgets if not w.parent()]
        if len(widgets) == 0:
            # Widget doesn't exist ==> we add the trip & all its picture groupe (easy)
            target_trip_widget = self.add_trip(target_trip)
            picture_groups = self.repository.trips[target_trip].values()
        else:
            # Widget exists ==> we need to add only the new picture group
            # There should be only 1 match
            target_trip_widget = widgets[0]
            picture_groups = self.repository.trips[target_trip].values()
            target_picture_group = [
                pg for pg in picture_groups if pg.name == picture_group_name
            ]
            picture_groups = [target_picture_group[0]]

        for picture_group in picture_groups:
            self.add_picture_group(target_trip_widget, picture_group)

    def set_folders(self, folders):
        """Defines which folders to display

        Parameters
        ----------
        folders : list of models.storagelocations.StorageLocations
            The list of folders to display as columns in the tree
        """
        logger.info(f"PicturesTree.set_folders: displaying {len(folders)} folders")
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
        logger.info("PicturesTree.fill_tree")
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
        logger.debug(f"PicturesTree.add_trip {trip}")
        data = [trip]
        trip_widget = QtWidgets.QTreeWidgetItem(data)
        self.addTopLevelItem(trip_widget)

        for column, field in enumerate(self.columns):
            trip_widget.setTextAlignment(column, field["alignment"])

        return trip_widget

    def add_picture_group(self, trip_widget, picture_group, picture_group_widget=None):
        """Adds or updates a single picture group to the tree

        Parameters
        ----------
        trip_widget : QtWidgets.QTreeWidgetItem
            The widget in which to add the picture group
        picture_group : models.picturegroup.PictureGroup
            The picture group to add to the tree
        picture_group_widget : QtWidgets.QTreeWidgetItem
            If provided, will update the item. Otherwise, creates a new one
        """
        try:
            trip_widget.data(0, Qt.DisplayRole)
        except RuntimeError:  # Widget has been deleted since then (race condition)
            return
        logger.debug(
            f"PicturesTree.add_picture_group: {picture_group.name} in {trip_widget.data(0, Qt.DisplayRole)}"
        )
        data = [picture_group.name]
        for column in self.columns[1:]:
            data.append(str(len(picture_group.locations.get(column["name"], []))))

        # Display data and connect to the signals in case of change
        if picture_group_widget:
            for col, column in enumerate(data):
                picture_group_widget.setText(col, data[col])
        else:
            picture_group_widget = QtWidgets.QTreeWidgetItem(data)
            picture_group.pictureAdded.connect(
                lambda _a, _b: self.add_picture_group(
                    trip_widget, picture_group, picture_group_widget
                )
            )
            picture_group.pictureRemoved.connect(
                lambda _a, _b: self.add_picture_group(
                    trip_widget, picture_group, picture_group_widget
                )
            )
            picture_group.pictureTasksDone.connect(
                lambda: self.add_picture_group(
                    trip_widget, picture_group, picture_group_widget
                )
            )
            picture_group.pictureTasksStart.connect(
                lambda: self.add_picture_group(
                    trip_widget, picture_group, picture_group_widget
                )
            )
            picture_group.pictureGroupDeleted.connect(
                lambda: self.remove_picture_group(picture_group_widget)
            )
            trip_widget.addChild(picture_group_widget)

        # Add tooltips
        for col, column in enumerate(self.columns[1:]):
            pictures = picture_group.locations.get(column["name"], [])
            if pictures:
                picture_group_widget.setToolTip(
                    col + 1, "\n".join([p.filename for p in pictures])
                )

        # Add "task in progress" icon
        if picture_group.tasks:
            logger.critical("Displaying tasks in progress")
            picture_group_widget.setData(
                0, Qt.DecorationRole, QtGui.QIcon("assets/images/hourglass.png")
            )
        else:
            picture_group_widget.setData(0, Qt.DecorationRole, QtCore.QVariant())

    def remove_picture_group(self, picture_group_widget):
        """Removes a picture group from the tree

        Also removes the top-level item (trip) if it becomes empty

        Parameters
        ----------
        picture_group_widget : QtWidgets.QTreeWidgetItem
            The picture group to remove
        """
        if picture_group_widget is None:
            return
        # This means it has been deleted from the tree before
        if picture_group_widget.parent() is None:
            return
        logger.debug(
            f"PicturesTree.remove_picture_group: {picture_group_widget.data(0, Qt.DisplayRole)} from {picture_group_widget.parent().data(0, Qt.DisplayRole)}"
        )
        trip_widget = picture_group_widget.parent()
        trip_widget.removeChild(picture_group_widget)
        if trip_widget.childCount() == 0:
            logger.info(
                f"PicturesTree.remove_picture_group: Removing trip {trip_widget.data(0, Qt.DisplayRole)}"
            )
            self.takeTopLevelItem(self.indexOfTopLevelItem(trip_widget))

    def on_item_clicked(self, item):
        """Item clicked ==> display corresponding images

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
            The item that was clicked"""
        # Exclude clicks on trips
        logger.info(f"PicturesTree.on_item_clicked: {item.data(0, Qt.DisplayRole)}")
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
    picture_added (picture, conversion_type)
        Adds a picture on display (used for signal processing)
    picture_removed (conversion_type, location)
        Removes a picture from display (used for signal processing)
    clear_display
        Removes all widgets from the display & deletes them properly
    generate_image (row, column)
        Generates an image for the provided row & column
    copy_image (row, column)
        Copies an image to the provided row & column
    delete_image (row, column)
        Deletes the image in the provided row & column
    """

    def __init__(self, parent_controller):
        """Stores reference to parent controller + initializes the display

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller"""
        logger.debug("PictureGrid.init")
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
            The group of pictures to display
        """
        logger.debug(
            f"PictureGrid.display_picture_group {picture_group.trip}/{picture_group.name}"
        )
        # TODO: Picture grid > Allow to filter which pictures to display (via checkbox)
        self.clear_display()
        self.picture_group = picture_group
        self.picture_group.pictureAdded.connect(self.picture_added)
        self.picture_group.pictureRemoved.connect(self.picture_removed)
        self.picture_group.pictureGroupDeleted.connect(self.clear_display)

        # Include locations from the DB + "" for the header
        rows = {"": ""}
        rows.update({l.name: l for l in self.database.storagelocations_get_folders()})

        # Include conversion types for existing pictures
        # "" is added for RAW files
        columns = [""] + list(self.picture_group.pictures.keys())
        # Add conversion types based on conversion methods
        columns = columns + [m.suffix for m in self.database.conversionmethods_get()]
        # "" is added for header row
        columns = [""] + sorted(set(columns))

        # Add row & column headers
        self.grid.append([])
        for column_name in columns:
            try:
                method = self.database.conversionmethods_get_by_suffix(column_name)
                label = QtWidgets.QLabel(method.name)
                label.model = method
            except:
                label = QtWidgets.QLabel(column_name)
            self.grid[0].append(label)

        for name in sorted(rows.keys()):
            if name == "":  # To avoid erasing the headers
                continue
            label = QtWidgets.QLabel(name)
            label.model = rows[name]
            self.grid.append([label])

        # Add the images themselves
        for column, conversion_type in enumerate(columns):
            for row, location_name in enumerate(sorted(rows.keys())):
                if column == 0 or row == 0:
                    self.ui["layout"].addWidget(self.grid[row][column], row, column)
                    self.grid[row][column].setProperty("class", "grid_header")
                    continue

                picture_container = PictureContainer(self, row, column)

                # No picture at all for this conversion type
                if conversion_type not in self.picture_group.pictures:
                    picture_container.set_empty_picture()
                else:
                    picture = [
                        p
                        for p in self.picture_group.pictures[conversion_type]
                        if p.location.name == location_name
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

        self.grid[0][1].setText(_("RAW"))

    def picture_added(self, picture, conversion_type):
        """Receives the signal from the picture_group

        Parameters
        ----------
        picture : models.picture.Picture
            The newly added picture
        conversion_type : str
            The suffix of the conversion type (as a picture_group.pictures key)
        """
        logger.debug(f"PictureGrid.picture_added {picture.filename}")
        self.display_picture_group(self.picture_group)

    def picture_removed(self, conversion_type, location):
        """Receives the signal from the picture_group

        Parameters
        ----------
        conversion_type : str
            The suffix of the conversion type (as a picture_group.pictures key)
        location : StorageLocation
            The storage location of the picture
        """
        logger.debug(
            f"PictureGrid.picture_removed {conversion_type} from {location.name}"
        )
        self.display_picture_group(self.picture_group)

    def clear_display(self):
        """Removes all widgets from the display & deletes them properly"""
        logger.info("PictureGrid.clear_display")
        for row in self.grid:
            for element in row:
                self.ui["layout"].removeWidget(element)
                element.deleteLater()
                element = None
        self.grid = []

        if self.picture_group:
            self.picture_group.pictureAdded.disconnect(self.picture_added)
            self.picture_group.pictureRemoved.disconnect(self.picture_removed)
            self.picture_group.pictureGroupDeleted.disconnect(self.clear_display)
            self.picture_group = None

    def generate_image(self, row, column):
        # TODO: Generate & copy image > merge actions? (& prioritize copy over generate)
        """Generates an image for the provided row & column

        Parameters
        ----------
        row : int
            The row in which to generate the image
        column : int
            The column in which to generate the image"""
        logger.debug(f"PictureGrid.generate_image row {row}, column {column}")

        target_location = self.grid[row][0].model
        try:
            method = self.grid[0][column].model
        except:
            self.picture_containers[row][column].display_error(
                _("No conversion method found")
            )
            return

        label = _("Convert 1 image in {location}").format(location=target_location.name)
        logger.info(
            f"PictureGrid.generate_image {self.picture_group.trip}/{self.picture_group.name} using {method} to {target_location.name}"
        )
        self.repository.generate_pictures(
            label, target_location, [method], picture_group=self.picture_group
        )
        # Updated data will be displayed through the signals directly

    def copy_image(self, row, column):
        """Copies an image to the provided row & column

        Parameters
        ----------
        row : int
            The row in which to copy the image
        column : int
            The column in which to copy the image"""
        logger.debug(f"PictureGrid.copy_image row {row}, column {column}")

        target_location = self.grid[row][0].model
        try:
            method = self.grid[0][column].model.suffix
        except:
            method = self.grid[0][column].text()
        if column == 1:
            method = ""  # RAW images, label is overridden in code

        try:
            label = _("Copy 1 image to {target}").format(target=target_location.name)
            logger.info(
                f"PictureGrid.copy_image {self.picture_group.trip}/{self.picture_group.name} using {method} to {target_location.name}"
            )
            self.repository.copy_pictures(
                label,
                target_location,
                picture_group=self.picture_group,
                conversion_method=method,
            )
            # Updated data will be displayed through the signals directly
        except FileNotFoundError as e:
            self.picture_containers[row][column].display_error("".join(e.args))

    def delete_image(self, row, column):
        """Deletes an image in the provided row & column

        Parameters
        ----------
        row : int
            The row in which to copy the image
        column : int
            The column in which to copy the image"""
        logger.debug(f"PictureGrid.delete_image row {row}, column {column}")

        picture = self.picture_containers[row][column].picture

        label = _("Remove 1 image in {target}").format(target=picture.location.name)
        logger.info(
            f"PictureGrid.delete_image {self.picture_group.trip}/{self.picture_group.name}/{picture.filename} in {picture.location.name}"
        )
        self.repository.remove_pictures(label, None, self.picture_group, picture)
        self.picture_containers[row][column].set_empty_picture()

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
        logger.debug(f"PictureContainer.init row {row}, column {column}")
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
        logger.debug(
            f"PictureContainer.set_empty_picture row {self.row}, column {self.column}"
        )
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
        logger.debug(
            f"PictureContainer.set_picture {picture.filename} in row {self.row}, column {self.column}"
        )
        self.clear_display()
        self.picture = picture

        self.ui["elements"]["filename"] = QtWidgets.QLabel(self.picture.filename)
        self.ui["layout"].addWidget(self.ui["elements"]["filename"])

        pixmap = QtGui.QPixmap(self.picture.path)
        # Image exists and can be read by PyQt5
        if pixmap.width() > 0:
            self.ui["elements"]["image"] = PictureDisplay()
            self.ui["elements"]["image"].image_path = self.picture.path
            self.ui["elements"]["image"].setPixmap(pixmap)
            self.ui["layout"].addWidget(self.ui["elements"]["image"])
        else:
            self.ui["elements"]["label"] = QtWidgets.QLabel(_("Image unreadable"))
            self.ui["elements"]["label"].setProperty("class", "small_note")
            self.ui["layout"].addWidget(self.ui["elements"]["label"])

        # Delete button
        # TODO: Ensure delete button is next to image (by default the image takes all the vertical space)
        self.ui["elements"]["delete"] = IconButton(
            QtGui.QIcon("assets/images/delete.png")
        )
        self.ui["elements"]["delete"].clicked.connect(lambda: self.on_click_delete())
        self.ui["layout"].addWidget(self.ui["elements"]["delete"])

    def on_click_generate(self):
        """Handler for generate button: triggers parent's handler"""
        logger.debug(
            f"PictureContainer.on_click_generate in row {self.row}, column {self.column}"
        )
        self.parent_controller.generate_image(self.row, self.column)

    def on_click_copy(self):
        """Handler for copy button: triggers parent's handler"""
        logger.debug(
            f"PictureContainer.on_click_copy in row {self.row}, column {self.column}"
        )
        self.parent_controller.copy_image(self.row, self.column)

    def on_click_delete(self):
        """Handler for delete button: deletes the image & refreshes the screen"""
        logger.debug(
            f"PictureContainer.on_click_delete in row {self.row}, column {self.column}"
        )
        dialog = QtWidgets.QMessageBox(self.ui["main"])
        dialog.setWindowTitle("Please confirm")
        dialog.setText("Do you really want to delete this image?")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        button = dialog.exec()

        if button == QtWidgets.QMessageBox.Yes:
            self.parent_controller.delete_image(self.row, self.column)

    def display_error(self, message):
        """Displays the provided error message

        Parameters
        ----------
        message : str
            The message to display
        """
        logger.debug(f"PictureContainer.display_error {message}")
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


# TODO: Allow to zoom on pictures (with sync between images)


class PicturesController:
    """Picture organization, selection & link to trips

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    code : str
        The internal name of this controller - used for references
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
    code = "Pictures"

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements.

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        logger.debug("PicturesController.init")
        self.parent_window = parent_window
        self.database = parent_window.database
        self.repository = parent_window.repository
        self.folders = []

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

        self.ui["picture_grid"] = PictureGrid(self)
        self.ui["right_layout"].addWidget(self.ui["picture_grid"].display_widget)

        # TODO: Pictures screen > display loading status for background tasks (progress bar)

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
        button.triggered.connect(lambda: self.parent_window.display_tab(self.code))
        return button

    def on_load_pictures(self):
        """User clicks 'load pictures' => reload the tree of pictures"""
        logger.debug(
            f"PicturesController.on_load_pictures on {len(self.folders)} folders"
        )
        self.repository.load_pictures()

        self.ui["picture_tree"].fill_tree()

    def refresh_folders(self):
        """Refreshes the list of folders from DB"""
        logger.debug("PicturesController.refresh_folders")
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
        logger.debug("PicturesController.refresh_display")
        # Refresh folder names
        self.refresh_folders()

        # Refresh image tree
        self.ui["picture_tree"].set_folders(self.folders)
        self.ui["picture_tree"].fill_tree()

    def display_picture_group(self, picture_group):
        """Displays pictures from a given group"""
        self.ui["picture_grid"].display_picture_group(picture_group)
