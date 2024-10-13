"""Splits the divelog scan in multiple images & prepares them for Subsurface import

Classes
----------
DiveTree
    The tree displaying the dives
PictureGrid
    Displays the split pictures from the dive log scan
PictureContainer
    Displays an image with the dive reference below
PictureDisplay
    Displays a single image while preserving aspect ratio when resizing
DivelogScanController
    Divelog scan split, organization & link to trips
"""

import os
import gettext
import logging
import piexif

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.basetreewidget import BaseTreeWidget
from controllers.widgets.pathselectbutton import PathSelectButton
from models.divelog import DiveLog
from models.storagelocation import StorageLocation as StorageLocationModel
from models.storagelocation import StorageLocationType

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
        Stores reference to parent controller & repository
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
        """Stores reference to parent controller

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
            widget.setIcon(
                4,
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/check.png"
                ),
            )
        else:
            widget.setIcon(
                4,
                QtGui.QIcon(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                    + "/assets/images/delete.png"
                ),
            )
        widget.setData(0, Qt.UserRole, dive)
        return widget


class PictureGrid:
    """Displays all split pictures from the main picture

    Attributes
    ----------
    parent_controller : PicturesController
        A reference to the parent controller
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen
    source_image : QtGui.QImage
        The original image (the paper divelog scan)

    Properties
    -------
    display_widget
        Returns the QtWidgets.QWidget for display of this element

    Methods
    -------
    __init__ (parent_controller)
        Stores reference to parent controller + initializes the display
    on_choose_scan_file
        Displays the divelog's 4 images after split
    clear_display
        Clears the display of images
    """

    y_split = 1143
    x_split = 810

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
            self.parent_controller.display_scan_file_error(
                _("Source file could not be read")
            )
            return
        self.parent_controller.display_scan_file_error()

        # Prepare rotation of image
        rotate = QtGui.QTransform()
        rotate.rotate(90)

        # Split it in 4 & rotate each one
        split_matrix = [
            [0, self.y_split, self.x_split, self.y_split],
            [self.x_split, self.y_split, self.x_split, self.y_split],
            [0, 0, self.x_split, self.y_split],
            [self.x_split, 0, self.x_split, self.y_split],
        ]
        for position, split in enumerate(split_matrix):
            image = self.source_image.copy(*split).transformed(rotate)
            if "picture_container" + str(position) in self.ui:
                self.ui["picture_container" + str(position)].set_image(image)
            else:
                widget = PictureContainer(image)
                self.ui["picture_container" + str(position)] = widget
                self.ui["layout"].addWidget(widget, position % 2, position // 2)

    def clear_display(self):
        """Clears the display of images"""
        for i in self.ui:
            if i.startswith("picture_container"):
                self.ui[i].set_image()

    def on_validate(self, target_folder, scan_file_split_mask):
        """Saves the 4 split images

        Parameters
        ----------
        target_folder : str
            The folder in which to save the images
        scan_file_split_mask : str
            The file name to use (processed by datetime.strftime)
        """
        logger.info(f"PictureGrid.on_validate {target_folder} {scan_file_split_mask}")
        for i in self.ui:
            if i.startswith("picture_container"):
                self.ui[i].on_validate(target_folder, scan_file_split_mask)

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this element"""
        return self.ui["main"]


class PictureContainer(QtWidgets.QWidget):
    """Displays an image with the dive reference below

    Attributes
    ----------
    original_image : QImage
        The image being displayed (without any scaling, transformation, ...)
    ui : dict of QtWidgets.QWidget
        The different widgets displayed on the screen


    Methods
    -------
    __init__ (image, *args, **kwargs)
        Initializes the widget & its child widgets
    set_image (image)
        Displays / updates the image being displayed
    on_validate (target_folder, scan_file_split_mask)
        Saves the image with matching EXIF data
    dragEnterEvent (event)
        Accepts drag enter events (without doing anything else)
    dropEvent (event)
        Stores the source dive data (& displays it) when dives are dragged here
    """

    def __init__(self, image, *args, **kwargs):
        """Initializes the widget & its child widgets

        Methods
        -------
        image : QImage
            The image data to display
        """
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.ui = {}
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.setLayout(self.ui["layout"])

        self.ui["picture_display"] = PictureDisplay()
        self.ui["layout"].addWidget(self.ui["picture_display"])

        self.ui["label"] = QtWidgets.QLabel()
        self.ui["layout"].addWidget(self.ui["label"])

        self.ui["error_label"] = QtWidgets.QLabel()
        self.ui["error_label"].setProperty("class", "validation_error")
        self.ui["error_label"].hide()
        self.ui["layout"].addWidget(self.ui["error_label"])

        self.set_image(image)

    def set_image(self, image=None):
        """Displays / updates the image being displayed

        Methods
        -------
        image : QImage
            The image data to display
        """
        self.original_image = image
        self.ui["picture_display"].original_image = image
        if image is None:
            self.ui["picture_display"].setPixmap(QtGui.QPixmap())
        else:
            self.ui["picture_display"].setPixmap(QtGui.QPixmap.fromImage(image))
            self.ui["picture_display"].scale_image()

    def on_validate(self, target_folder, scan_file_split_mask):
        """Saves the image with matching EXIF data

        Parameters
        ----------
        target_folder : str
            The folder in which to save the images
        scan_file_split_mask : str
            The file name to use (processed by datetime.strftime)
        """
        logger.debug(
            f"PictureContainer.on_validate {target_folder} {scan_file_split_mask}"
        )
        dive = self.property("dive")
        if not dive:
            return

        # Save the image
        filename = dive.start_date.strftime(scan_file_split_mask)
        file_path = os.path.join(target_folder, filename)
        error = None
        if os.path.exists(file_path):
            error = _(f"File {filename} already exists")
        if not self.original_image.save(file_path):
            error = _(f"Could not save {filename}")

        if error is not None:
            self.ui["error_label"].setText(error)
            self.ui["error_label"].show()
            return
        else:
            self.ui["error_label"].setText("")
            self.ui["error_label"].hide()

        # Change EXIF data
        picture_data = piexif.load(file_path)
        start_date = dive.start_date.strftime("%Y:%m:%d %H:%M:%S")
        picture_data["0th"][piexif.ImageIFD.DateTime] = start_date
        picture_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = start_date
        picture_data["Exif"][piexif.ExifIFD.DateTimeDigitized] = start_date
        exif_bytes = piexif.dump(picture_data)
        piexif.insert(exif_bytes, file_path)

        # Display dive info normally (no class, no star)
        self.ui["label"].setProperty("class", "")
        self.ui["label"].setText(f"Dive {dive.number} on {dive.start_date}")
        self.ui["label"].style().unpolish(self.ui["label"])
        self.ui["label"].style().polish(self.ui["label"])

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
        self.setProperty("dive", dive)

        self.ui["label"].setProperty("class", "has_pending_changes")
        self.ui["label"].setText(f"*Dive {dive.number} on {dive.start_date}")
        self.ui["label"].style().unpolish(self.ui["label"])
        self.ui["label"].style().polish(self.ui["label"])


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
        self.scale_image()

    def scale_image(self):
        self.pixmap().swap(
            QtGui.QPixmap.fromImage(self.original_image).scaled(
                self.width(), self.height(), Qt.KeepAspectRatio
            )
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
    database : models.database.Database
        The application's database
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
    target_folder : models.storagelocation.StorageLocation
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
    display_scan_file_error (error)
        Displays an error next to the scan file selector
    display_target_folder_error (error)
        Displays an error next to the target folder selector
    on_choose_scan_file
        Triggers the split of the divelog scan image when user chooses it
    on_choose_target_folder
        Stores the folder in which split images should be saved (& saves it in DB)
    on_validate
        Moves, renames and changes split image EXIF data according to user selection
    refresh_display
        Refreshes the display - reloads the list of dives
    """

    name = _("Divelog scan split")
    code = "DivelogScan"
    scan_file_split_mask = "%Y-%m-%d %Hh%M - Carnet.jpg"

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
        self.target_folder = self.database.storagelocations_get_target_scan_folder()
        if self.target_folder is None:
            self.target_folder = StorageLocationModel()
            self.target_folder.name = "Target scan folder"
            self.target_folder.type = StorageLocationType["target_scan_folder"]

        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        ###### Top part: File to split ####
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
        self.ui["scan_file_path_error"].setProperty("class", "validation_error")
        self.ui["scan_file_path_error"].hide()
        self.ui["scan_file_wrapper_layout"].addWidget(self.ui["scan_file_path_error"])
        # File path selector
        self.ui["scan_file_path_change"] = PathSelectButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/modify.png"
            ),
            self.ui["main"],
            "file",
        )
        self.ui["scan_file_path_change"].pathSelected.connect(self.on_choose_scan_file)
        self.ui["top_layout"].addWidget(self.ui["scan_file_path_change"])

        ###### Top part: Display of pictures & dives ####
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

        ###### Bottom part: Target folder and Validate button ####
        # Bottom part: Target folder and Validate button
        self.ui["bottom"] = QtWidgets.QWidget()
        self.ui["bottom_layout"] = QtWidgets.QHBoxLayout()
        self.ui["bottom"].setLayout(self.ui["bottom_layout"])
        self.ui["layout"].addWidget(self.ui["bottom"])

        # Folder label
        self.ui["target_folder_label"] = QtWidgets.QLabel(_("Target scan folder"))
        self.ui["bottom_layout"].addWidget(self.ui["target_folder_label"], 1)

        # Folder path wrapper
        self.ui["target_folder_wrapper"] = QtWidgets.QWidget()
        self.ui["target_folder_layout"] = QtWidgets.QVBoxLayout()
        self.ui["target_folder_wrapper"].setLayout(self.ui["target_folder_layout"])
        self.ui["bottom_layout"].addWidget(self.ui["target_folder_wrapper"], 2)
        # Folder path
        self.ui["target_folder"] = QtWidgets.QLineEdit(self.target_folder.path)
        self.ui["target_folder"].setEnabled(False)
        self.ui["target_folder_layout"].addWidget(self.ui["target_folder"])
        # Folder path error
        self.ui["target_folder_error"] = QtWidgets.QLabel()
        self.ui["target_folder_error"].setProperty("class", "validation_error")
        self.ui["target_folder_error"].hide()
        self.ui["target_folder_layout"].addWidget(self.ui["target_folder_error"])
        # Folder path selector
        self.ui["target_folder_change"] = PathSelectButton(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/modify.png"
            ),
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

    def display_scan_file_error(self, error=None):
        """Displays an error next to the scan file selector

        Parameters
        ----------
        error : str
            The error to display
        """
        if error is None:
            self.ui["scan_file_path_error"].setText("")
            self.ui["scan_file_path_error"].hide()
        else:
            self.ui["scan_file_path_error"].setText(error)
            self.ui["scan_file_path_error"].show()
            self.picture_grid.clear_display()

    def display_target_folder_error(self, error=None):
        """Displays an error next to the target folder selector

        Parameters
        ----------
        error : str
            The error to display
        """
        if error is None:
            self.ui["target_folder_error"].setText("")
            self.ui["target_folder_error"].hide()
        else:
            self.ui["target_folder_error"].setText(error)
            self.ui["target_folder_error"].show()

    def on_choose_scan_file(self, path):
        """Triggers the split of the divelog scan image when user chooses it

        Parameters
        ----------
        path : str
            The path of the divelog scan image
        """
        self.divelog_scan_file = path
        self.ui["scan_file_path"].setText(path)
        self.display_scan_file_error()

        self.picture_grid.on_choose_scan_file(self.divelog_scan_file)

    def on_choose_target_folder(self, path):
        """Stores the folder in which split images should be saved

        Parameters
        ----------
        path : str
            The path of the target folder
        """

        # Save in DB
        self.target_folder.path = path
        if path:
            self.database.session.add(self.target_folder)
            self.database.session.commit()
            logger.info(
                f"DivelogScanController.on_choose_target_folder New folder created {self.target_folder}"
            )

        self.ui["target_folder"].setText(path)
        self.display_target_folder_error()

    def on_validate(self):
        """Moves, renames and changes split image EXIF data according to user selection"""
        target_folder = self.ui["target_folder"].text()
        if target_folder == "":
            self.display_target_folder_error(_("Please choose a target folder"))
            return
        else:
            self.display_target_folder_error()
        self.picture_grid.on_validate(target_folder, self.scan_file_split_mask)

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        return self.ui["main"]

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/divelog.png"
            ),
            self.name,
            self.parent_window,
        )
        button.setStatusTip(_("Divelog scan split"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.code))
        return button

    def refresh_display(self):
        """Refreshes the display - reloads the list of dives"""
        logger.debug("DivelogScanController.refresh_display")

        # Reload divelog data
        divelog = self.database.storagelocations_get_divelog()
        self.divelog_path = divelog[0].path if divelog[0].path != " " else None
        try:
            self.divelog.load_dives(self.divelog_path)
            self.dive_tree.fill_tree()
        except (IOError, ValueError) as e:
            self.display_scan_file_error(e.args[0])

        # Reload divelog scan target folder
        target_folder = self.database.storagelocations_get_target_scan_folder()
        self.target_folder = target_folder
        if target_folder is None:
            self.ui["target_folder"].setText("")
        else:
            self.ui["target_folder"].setText(target_folder.path)
