"""Splits the divelog scan in multiple images & prepares them for Subsurface import

Classes
----------
DiveTree
    The tree displaying the dives
PictureGrid
    Displays the split pictures from the dive log scan
DivelogScanController
    Divelog scan split, organization & link to trips
"""
import gettext
import logging

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.basetreewidget import BaseTreeWidget
from controllers.widgets.iconbutton import IconButton
from controllers.widgets.pathselectbutton import PathSelectButton
from models.divelog import DiveLog

_ = gettext.gettext
logger = logging.getLogger(__name__)


class DiveTree(BaseTreeWidget):
    """The tree displaying the dives

    Attributes
    ----------
    columns : dict
        The columns to display in the tree
    parent_controller : PicturesController
        A reference to the parent controller
    divelog: models.divelog.DiveLog
        The divelog to display

    Methods
    -------
    __init__ (parent_controller)
        Stores reference to parent controller & repository + sets up event handlers
    fill_tree
        Adds all trips & dives to the tree
    dive_to_widget (dive)
        Converts a Dive object to a QTreeWidgetItem
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.35,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Date"),
            "size": 0.25,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Depth"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Duration"),
            "size": 0.2,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Picture"),
            "size": 0.1,
            "alignment": Qt.AlignCenter,
        },
    ]

    def __init__(self, parent_controller):
        """Stores reference to parent controller + sets up event handlers

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller
        """
        logger.debug("DiveTree.init")
        super().__init__(parent_controller)
        self.parent_controller = parent_controller
        self.divelog = parent_controller.divelog
        self.setSortingEnabled(False)
        self.setMinimumSize(600, 100)
        self.setDragEnabled(True)

    def fill_tree(self):
        """Adds all trips & dives to the tree"""
        logger.info("DiveTree.fill_tree")
        self.clear()
        for element in reversed(self.divelog.dives):
            if element.type == "dive":
                widget = self.dive_to_widget(element)
                self.addTopLevelItem(widget)
            elif element.type == "trip":
                data = [element.name]
                widget = QtWidgets.QTreeWidgetItem(map(str, data))
                widget.setData(0, Qt.UserRole, element)
                # Disable drag / drop for trips
                widget.setFlags(widget.flags() ^ Qt.ItemIsDragEnabled)
                self.addTopLevelItem(widget)
                for dive in reversed(element.dives):
                    dive_widget = self.dive_to_widget(dive)
                    widget.addChild(dive_widget)

    def dive_to_widget(self, dive):
        """Converts a Dive object to a QTreeWidgetItem

        Parameters
        ----------
        dive : Dive
            A dive to convert

        Returns
        ----------
        QtWidgets.QTreeWidgetItem
            The item to display in the tree
        """
        start = QtCore.QDateTime.fromString(dive.start_date.isoformat(), Qt.ISODate)
        data = [
            dive.number,
            start.toString(Qt.SystemLocaleShortDate),
            int(dive.max_depth),
            dive.duration,
            "",
        ]
        widget = QtWidgets.QTreeWidgetItem(map(str, data))
        if dive.has_picture:
            widget.setIcon(4, QtGui.QIcon("assets/images/check.png"))
        else:
            widget.setIcon(4, QtGui.QIcon("assets/images/delete.png"))
        widget.setData(0, Qt.UserRole, dive)
        return widget


class PictureGrid:
    """Displays all split pictures from the main picture

    Attributes
    ----------
    parent_controller : PicturesController
        A reference to the parent controller
    grid : dict of dict of QtWidgets.QLabel or QtWidgets.QWidget
        The different headers & images to display
    pictures : dict of dict of PictureDisplay
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
    on_choose_scan_file
        Displays the divelog's 4 images after split
    clear_display
        Clears the display of images
    """

    y_split = 1120
    x_split = 755

    def __init__(self, parent_controller):
        """Stores reference to parent controller + initializes the display

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller"""
        logger.debug("PictureGrid.init")
        self.parent_controller = parent_controller

        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QGridLayout()
        self.ui["main"].setProperty("class", "picture_grid")
        self.ui["main"].setLayout(self.ui["layout"])

    def on_choose_scan_file(self, path):
        """Displays the divelog's 4 images after split

        Parameters
        ----------
        path : str
            The path of the source image file
        """
        logger.debug("PictureGrid.on_choose_scan_file")
        self.source_image = QtGui.QImage(path)
        if self.source_image.isNull():
            # TODO: display an error in this case
            self.parent_controller.display_scan_file_error(
                _("Source file could not be read")
            )
            return
        self.parent_controller.display_scan_file_error("")

        # Rotate the image 90 degrees
        rotate = QtGui.QTransform()
        rotate.rotate(90)
        rotated_image = self.source_image.transformed(rotate)

        # Then split it in 4
        split_matrix = [
            [0, self.y_split, self.x_split, self.y_split],
            [self.x_split, self.y_split, self.x_split, self.y_split],
            [0, 0, self.x_split, self.y_split],
            [self.x_split, 0, self.x_split, self.y_split],
        ]
        for position, split in enumerate(split_matrix):
            image = self.source_image.copy(*split).transformed(rotate)
            widget = PictureContainer()
            self.ui["picture_container" + str(position)] = widget
            widget.setAcceptDrops(True)
            layout = QtWidgets.QVBoxLayout()
            widget.setLayout(layout)

            picture = PictureDisplay()
            self.ui["picture_display" + str(position)] = picture
            picture.setPixmap(QtGui.QPixmap.fromImage(image))
            layout.addWidget(picture, 1)

            label = QtWidgets.QLabel()
            layout.addWidget(label)

            self.ui["layout"].addWidget(widget, position % 2, position // 2)

    def clear_display(self):
        """Clears the display of images"""
        for i in self.ui:
            if not i.startswith("picture_display"):
                continue
            self.ui[i].setPixmap(QtGui.QPixmap())

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        return self.ui["main"]


class PictureContainer(QtWidgets.QWidget):
    """Displays an image with the dive reference below

    Methods
    -------
    dragEnterEvent (event)
        Accepts drag enter events (without doing anything else)
    dropEvent (event)
        Stores the source dive data (& displays it) when dives are dragged here
    """

    def dragEnterEvent(self, event):
        """Accepts drag enter events (without doing anything else)

        Parameters
        ----------
        event : QtGui.QDragEnterEvent
            The drag enter event
        """
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Stores the source dive data (& displays it) when dives are dragged here

        Parameters
        ----------
        event : QtGui.QDropEvent
            The drop event
        """
        logger.debug("PictureContainer.dropEvent")
        source_item = event.source().selectedItems()[0]
        dive = source_item.data(0, Qt.UserRole)
        self.layout().itemAt(1).widget().setText(
            f"Dive {dive.number} on {dive.start_date}"
        )
        self.setProperty("dive", dive)


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
                self.pixmap().scaled(self.width(), self.height(), Qt.KeepAspectRatio)
            )


class DivelogScanController:
    """Divelog scan split, organization & link to trips

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
    code : str
        The internal name of this controller - used for references
    parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
        The window displaying this controller
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen
    divelog_path : str
        Path to the divelog file
    divelog : models.divelog.DiveLog
        The divelog as application model
    picture_grid : PictureGrid
        The grid of pictures displayed (split of the divelog scan)
    dive_tree : DiveTree
        The tree of trips & dives displayed
    divelog_scan_file : str
        The original scan of the divelog
    divelog_scan_target_folder : str
        Where the split images should be stored

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
    on_choose_scan_file
        Triggers the split of the divelog scan image when user chooses it
    on_choose_target_folder
        Stores the folder in which split images should be saved
    on_validate
        Moves, renames and changes split image EXIF data according to user selection
    refresh_display
        Refreshes the display - reloads the list of dives
    """

    name = _("Divelog scan split")
    code = "DivelogScan"

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements.

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        logger.debug("DivelogScanController.init")
        self.parent_window = parent_window
        self.database = parent_window.database
        self.divelog_path = None
        self.divelog = DiveLog()
        self.picture_grid = PictureGrid(self)
        self.dive_tree = DiveTree(self)

        self.divelog_scan_file = ""
        self.divelog_scan_target_folder = ""

        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        # Top part: File to split
        self.ui["top"] = QtWidgets.QWidget()
        self.ui["top_layout"] = QtWidgets.QHBoxLayout()
        self.ui["top"].setLayout(self.ui["top_layout"])
        self.ui["layout"].addWidget(self.ui["top"])
        # File label
        self.ui["scan_file_label"] = QtWidgets.QLabel(_("Divelog scan to split"))
        self.ui["top_layout"].addWidget(self.ui["scan_file_label"], 1)
        # File path wrapper
        self.ui["scan_file_wrapper"] = QtWidgets.QWidget()
        self.ui["scan_file_wrapper_layout"] = QtWidgets.QVBoxLayout()
        self.ui["scan_file_wrapper"].setLayout(self.ui["scan_file_wrapper_layout"])
        self.ui["top_layout"].addWidget(self.ui["scan_file_wrapper"], 3)
        # File path
        self.ui["scan_file_path"] = QtWidgets.QLineEdit()
        self.ui["scan_file_path"].setEnabled(False)
        self.ui["scan_file_wrapper_layout"].addWidget(self.ui["scan_file_path"])
        # File path error
        self.ui["scan_file_path_error"] = QtWidgets.QLabel()
        self.ui["scan_file_path_error"].setProperty("class", "validation_warning")
        self.ui["scan_file_path_error"].hide()
        self.ui["scan_file_wrapper_layout"].addWidget(self.ui["scan_file_path_error"])
        # File path selector
        self.ui["scan_file_path_change"] = PathSelectButton(
            QtGui.QIcon("assets/images/modify.png"),
            self.ui["main"],
            "file",
        )
        self.ui["scan_file_path_change"].pathSelected.connect(self.on_choose_scan_file)
        self.ui["top_layout"].addWidget(self.ui["scan_file_path_change"])

        # Middle part: Display of pictures & dives
        self.ui["middle"] = QtWidgets.QWidget()
        self.ui["middle_layout"] = QtWidgets.QHBoxLayout()
        self.ui["middle"].setLayout(self.ui["middle_layout"])
        self.ui["layout"].addWidget(self.ui["middle"], 1)
        # Picture display
        self.ui["picture_grid"] = self.picture_grid.display_widget
        self.ui["middle_layout"].addWidget(self.ui["picture_grid"], 3)
        # Dive tree
        self.ui["dive_tree"] = self.dive_tree
        self.ui["middle_layout"].addWidget(self.ui["dive_tree"], 1)

        # Bottom part: Target folder and Validate button
        self.ui["bottom"] = QtWidgets.QWidget()
        self.ui["bottom_layout"] = QtWidgets.QHBoxLayout()
        self.ui["bottom"].setLayout(self.ui["bottom_layout"])
        self.ui["layout"].addWidget(self.ui["bottom"])
        # Folder label
        self.ui["target_folder_label"] = QtWidgets.QLabel(_("Target scan folder"))
        self.ui["bottom_layout"].addWidget(self.ui["target_folder_label"], 1)
        # Folder path
        self.ui["divelog_scan_target_folder"] = QtWidgets.QLineEdit()
        self.ui["divelog_scan_target_folder"].setEnabled(False)
        self.ui["bottom_layout"].addWidget(self.ui["divelog_scan_target_folder"], 2)
        # Folder path selector
        self.ui["target_folder_change"] = PathSelectButton(
            QtGui.QIcon("assets/images/modify.png"),
            self.ui["main"],
            "folder",
        )
        self.ui["target_folder_change"].pathSelected.connect(
            self.on_choose_target_folder
        )
        self.ui["bottom_layout"].addWidget(self.ui["target_folder_change"])
        # Separator
        self.ui["bottom_layout"].addStretch(2)
        # Validate button
        self.ui["validate"] = QtWidgets.QPushButton(_("Validate"))
        self.ui["validate"].clicked.connect(self.on_validate)
        self.ui["bottom_layout"].addWidget(self.ui["validate"])

    def display_scan_file_error(self, error):
        """Triggers the split of the divelog scan image when user chooses it

        Parameters
        ----------
        path : str
            The path of the divelog scan image
        """
        if error == "":
            self.ui["scan_file_path_error"].setText("")
            self.ui["scan_file_path_error"].hide()
        else:
            self.ui["scan_file_path_error"].setText(error)
            self.ui["scan_file_path_error"].show()
            self.picture_grid.clear_display()

    def on_choose_scan_file(self, path):
        """Triggers the split of the divelog scan image when user chooses it

        Parameters
        ----------
        path : str
            The path of the divelog scan image
        """
        self.divelog_scan_file = path
        self.ui["scan_file_path"].setText(path)

        self.picture_grid.on_choose_scan_file(self.divelog_scan_file)

    def on_choose_target_folder(self, path):
        """Stores the folder in which split images should be saved

        Parameters
        ----------
        path : str
            The path of the target folder
        """
        self.divelog_scan_target_folder = path
        self.ui["divelog_scan_target_folder"].setText(path)

    def on_validate(self):
        """Moves, renames and changes split image EXIF data according to user selection"""
        # TODO: Trigger the move & rename of images + EXIF data
        pass

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        divelog = self.database.storagelocations_get_divelog()
        if divelog:
            self.divelog_path = divelog[0].path
        else:
            self.divelog_path = None
        self.divelog.load_dives(self.divelog_path)

        self.dive_tree.fill_tree()

        return self.ui["main"]

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/divelog.png"), self.name, self.parent_window
        )
        button.setStatusTip(_("Organize divelog scans"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.code))
        return button

    def refresh_display(self):
        """Refreshes the display - reloads the list of dives"""
        logger.debug("DivelogScanController.refresh_display")

        divelog = self.database.storagelocations_get_divelog()
        if divelog:
            self.divelog_path = divelog[0].path
        else:
            self.divelog_path = None
        self.divelog.load_dives(self.divelog_path)

        self.dive_tree.fill_tree()
