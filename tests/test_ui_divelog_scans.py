import os
import sys
import pytest
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.divelog
from controllers.widgets.pathselectbutton import PathSelectButton


class TestUiDivelogScans:
    @pytest.fixture
    def pydive_divelog_scans(self, qtbot, pydive_mainwindow, pydive_divelog):
        pydive_mainwindow.display_tab("DivelogScan")

        yield pydive_mainwindow.layout.currentWidget().layout()

    def drag_drop(self, source, target):
        pos = target.pos()
        dropActions = Qt.CopyAction
        QMimeData = QtCore.QMimeData()
        QtMouseButtons = Qt.LeftButton
        QtKeyboardModifiers = Qt.NoModifier
        QEventType = QtCore.QEvent.Drop
        drop_event = QtGui.QDropEvent(
            pos, dropActions, QMimeData, QtMouseButtons, QtKeyboardModifiers, QEventType
        )
        drop_event.source = lambda: source
        return drop_event

    def test_divelogscans_display(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Check overall structure
        assert isinstance(divelogScanLayout, QtWidgets.QVBoxLayout), "Layout is OK"
        assert divelogScanLayout.count() == 3, "Count of elements is OK"

        # Check top part
        part = "Top part - "
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        assert isinstance(topLayout, QtWidgets.QHBoxLayout), part + "Layout is OK"
        assert topLayout.count() == 3, part + "Count of elements is OK"
        file_name = topLayout.itemAt(0).widget()
        assert isinstance(file_name, QtWidgets.QLabel), part + "Name is a QLabel"
        assert file_name.text() == "Divelog scan to split", part + "Name text is OK"
        path_wrapper = topLayout.itemAt(1).widget()
        assert isinstance(file_name, QtWidgets.QWidget), part + "Wrapper exists"
        path_display = path_wrapper.layout().itemAt(0).widget()
        assert isinstance(path_display, QtWidgets.QLineEdit), (
            part + "Path is a QLineEdit"
        )
        assert path_display.text() == "", part + "Path text is OK"
        path_error_display = path_wrapper.layout().itemAt(1).widget()
        assert isinstance(path_error_display, QtWidgets.QLabel), (
            part + "Error is a QLabel"
        )
        assert path_error_display.text() == "", part + "Error text is OK"
        path_change = topLayout.itemAt(2).widget()
        assert isinstance(path_change, PathSelectButton), (
            part + "Path change is PathSelectButton"
        )
        assert path_change.target_type == "file", part + "Path change looks for files"

        # Check middle part
        part = "Middle part - "
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        assert isinstance(middleLayout, QtWidgets.QHBoxLayout), part + "Layout is OK"
        assert middleLayout.count() == 2, part + "Count of elements is OK"
        picture_grid = middleLayout.itemAt(0).widget()
        assert isinstance(picture_grid, QtWidgets.QWidget), (
            part + "Picture grid is QWidget"
        )
        assert isinstance(picture_grid.layout(), QtWidgets.QGridLayout), (
            part + "Picture grid layout OK"
        )
        # Details of picture grid layout are done in separate function
        part = "Middle part - Dive tree - "
        dive_tree = middleLayout.itemAt(1).widget()
        assert isinstance(dive_tree, QtWidgets.QTreeWidget), part + "Is QTreeWidget"
        assert dive_tree.topLevelItemCount() == 8, part + "Count of elements OK"
        types = ["dive", "dive", "trip", "trip", "dive", "trip", "dive", "dive"]
        for i, expected_type in enumerate(types):
            tree_type = dive_tree.topLevelItem(i).data(0, Qt.UserRole)
            if expected_type == "trip":
                assert isinstance(tree_type, models.divelog.DiveTrip), (
                    part + "Item type is OK"
                )
                assert dive_tree.topLevelItem(i).childCount() > 0, (
                    part + "Item has children"
                )
            elif expected_type == "dive":
                assert isinstance(tree_type, models.divelog.Dive), (
                    part + "Item type is OK"
                )

        # Check bottom part
        part = "Bottom part - "
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        assert isinstance(bottomLayout, QtWidgets.QHBoxLayout), part + "Layout is OK"
        assert bottomLayout.count() == 5, part + "Count of elements is OK"
        folder_name = bottomLayout.itemAt(0).widget()
        assert isinstance(folder_name, QtWidgets.QLabel), part + "Name is a QLabel"
        assert folder_name.text() == "Target scan folder", part + "Name text is OK"
        path_wrapper = bottomLayout.itemAt(1).widget()
        assert isinstance(folder_name, QtWidgets.QWidget), part + "Wrapper exists"
        path_display = path_wrapper.layout().itemAt(0).widget()
        assert isinstance(path_display, QtWidgets.QLineEdit), (
            part + "Path is a QLineEdit"
        )
        assert path_display.text() == pytest.BASE_FOLDER, part + "Path text is OK"
        path_error_display = path_wrapper.layout().itemAt(1).widget()
        assert isinstance(path_error_display, QtWidgets.QLabel), (
            part + "Error is a QLabel"
        )
        assert path_error_display.text() == "", part + "Error text is OK"
        path_change = bottomLayout.itemAt(2).widget()
        assert isinstance(path_change, PathSelectButton), (
            part + "Path change is PathSelectButton"
        )
        assert path_change.target_type == "folder", (
            part + "Path change looks for folders"
        )
        spacer = bottomLayout.itemAt(3)
        assert isinstance(spacer, QtWidgets.QSpacerItem), part + "Spacer exists"
        validate = bottomLayout.itemAt(4).widget()
        assert isinstance(validate, QtWidgets.QPushButton), (
            part + "Validate is a QPushButton"
        )
        assert validate.text() == "Validate", part + "Validate text is OK"

    def test_divelogscans_display_no_target_folder(
        self, pydive_empty_db, pydive_mainwindow_empty_db
    ):
        pydive_mainwindow_empty_db.display_tab("DivelogScan")
        divelogScanLayout = pydive_mainwindow_empty_db.layout.currentWidget().layout()

        # Check dive tree is empty
        part = "Middle part - Dive tree - "
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        dive_tree = middleLayout.itemAt(1).widget()
        assert isinstance(dive_tree, QtWidgets.QTreeWidget), part + "Is QTreeWidget"
        assert dive_tree.topLevelItemCount() == 0, part + "Count of elements OK"

    def test_divelogscans_display_with_divelog_target_folder(
        self, pydive_db, pydive_divelog_scans
    ):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Check folder path displays correct path
        part = "Bottom part - "
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        path_wrapper = bottomLayout.itemAt(1).widget()
        path_display = path_wrapper.layout().itemAt(0).widget()
        assert path_display.text() == os.path.join(pytest.BASE_FOLDER), (
            part + "Path text is OK"
        )

    def test_divelogscans_load_picture(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        # Force reload of the same info (to check if it handles it well)
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Check overall display
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        picture_grid = middleLayout.itemAt(0).widget()
        picture_grid_layout = picture_grid.layout()
        assert picture_grid_layout.columnCount() == 2, "Picture grid - Column count OK"
        assert picture_grid_layout.rowCount() == 2, "Picture grid - Row count OK"

        # Check one of the images
        part = "Picture container - "
        picture_container = picture_grid_layout.itemAtPosition(1, 0).widget()
        assert isinstance(picture_container, QtWidgets.QWidget), part + "Is QWidget"
        picture_container_layout = picture_container.layout()
        assert isinstance(picture_container_layout, QtWidgets.QVBoxLayout), (
            part + "Layout OK"
        )
        assert picture_container_layout.count() == 3, part + "Element count OK"
        picture = picture_container_layout.itemAt(0).widget()
        assert isinstance(picture, QtWidgets.QLabel), part + "Picture widget OK"
        assert picture.text() == "", part + "Picture has no text"
        label = picture_container_layout.itemAt(1).widget()
        assert isinstance(label, QtWidgets.QLabel), part + "Error widget OK"
        assert label.text() == "", part + "Error has no text"
        error = picture_container_layout.itemAt(2).widget()
        assert isinstance(error, QtWidgets.QLabel), part + "Error widget OK"
        assert error.text() == "", part + "Error has no text"

    def test_divelogscans_load_picture_twice_then_error(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        path_change.pathSelected.emit(pytest.DIVELOG_FILE)

    def test_divelogscans_load_picture_error(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Check overall structure
        assert isinstance(divelogScanLayout, QtWidgets.QVBoxLayout), "Layout is OK"
        assert divelogScanLayout.count() == 3, "Count of elements is OK"

        # Load non-image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_FILE)

        # Check error display
        path_wrapper = topLayout.itemAt(1).widget()
        path_error = path_wrapper.layout().itemAt(1).widget()
        assert path_error.text() == "Source file could not be read", "Error text is OK"

    def test_divelogscans_link_picture_dive(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Get a dive (and select it for future use)
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        dive_tree = middleLayout.itemAt(1).widget()
        dive_item = dive_tree.topLevelItem(0)
        dive_tree.setCurrentItem(dive_item)

        # Get a picture element
        picture_grid = middleLayout.itemAt(0).widget()
        picture_container = picture_grid.layout().itemAtPosition(1, 0).widget()
        picture = picture_container.layout().itemAt(0).widget()
        label = picture_container.layout().itemAt(1).widget()
        error = picture_container.layout().itemAt(2).widget()

        # Simulate drag / drop of the dive to the picture (by direct call to dropEvent)
        # Drag and drop can't be tested (thanks to bug QTBUG-5232) so this is a workaround
        drop_event = self.drag_drop(dive_tree, picture)
        picture_container.dropEvent(drop_event)

        # Check results
        assert label.text() == "*Dive 172 on 2022-04-09 16:45:55", "Dive data is OK"
        assert error.text() == "", "Dive error is empty"

    def test_divelogscans_choose_target(self, pydive_divelog_scans):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Get widgets
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        path_wrapper = bottomLayout.itemAt(1).widget()
        path_display = path_wrapper.layout().itemAt(0).widget()
        path_change = bottomLayout.itemAt(2).widget()

        # Choose a folder
        path_change.pathSelected.emit(pytest.BASE_FOLDER)
        assert path_display.text() == pytest.BASE_FOLDER, "Path display updated"

    def test_divelogscans_validate(self, pydive_db, pydive_divelog_scans, qtbot):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Get a dive (and select it for future use)
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        dive_tree = middleLayout.itemAt(1).widget()
        dive_item = dive_tree.topLevelItem(0)
        dive_tree.setCurrentItem(dive_item)

        # Get a picture element
        picture_grid = middleLayout.itemAt(0).widget()
        picture_container = picture_grid.layout().itemAtPosition(1, 0).widget()
        picture = picture_container.layout().itemAt(0).widget()
        label = picture_container.layout().itemAt(1).widget()
        error = picture_container.layout().itemAt(2).widget()

        # Drag a dive to the image
        drop_event = self.drag_drop(dive_tree, picture)
        picture_container.dropEvent(drop_event)

        # Trigger the validation
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        validate = bottomLayout.itemAt(4).widget()
        qtbot.mouseClick(validate, Qt.LeftButton)

        # Check results
        new_file_path = os.path.join(
            pytest.BASE_FOLDER, "2022-04-09 16h45 - Carnet.jpg"
        )

        assert label.text() == "Dive 172 on 2022-04-09 16:45:55", "Dive data is OK"
        assert error.text() == "", "Dive error is empty"
        assert os.path.exists(new_file_path), "Split image saved"

    def test_divelogscans_validate_file_exists(
        self, pydive_db, pydive_divelog_scans, qtbot
    ):
        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Get a dive (and select it for future use)
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        dive_tree = middleLayout.itemAt(1).widget()
        dive_item = dive_tree.topLevelItem(0)
        dive_tree.setCurrentItem(dive_item)

        # Get a picture element
        picture_grid = middleLayout.itemAt(0).widget()
        picture_container = picture_grid.layout().itemAtPosition(1, 0).widget()
        picture = picture_container.layout().itemAt(0).widget()
        error = picture_container.layout().itemAt(2).widget()

        # Drag a dive to the image
        drop_event = self.drag_drop(dive_tree, picture)
        picture_container.dropEvent(drop_event)

        # Trigger the validation twice, so that the target file already exists
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        validate = bottomLayout.itemAt(4).widget()
        qtbot.mouseClick(validate, Qt.LeftButton)
        qtbot.mouseClick(validate, Qt.LeftButton)

        # Check results
        assert (
            error.text() == "File 2022-04-09 16h45 - Carnet.jpg already exists"
        ), "Dive error is OK"

    def test_divelogscans_validate_folder_does_not_exist(
        self, pydive_db, pydive_divelog_scans, pydive_mainwindow, qtbot
    ):
        existing_location = pydive_db.storagelocations_get_target_scan_folder()
        existing_location.path = os.path.join(pytest.BASE_FOLDER, "Inexistant")
        pydive_db.session.add(existing_location)
        pydive_db.session.commit()
        # Force screen refresh
        pydive_mainwindow.display_tab("DivelogScan")

        divelogScanLayout = pydive_divelog_scans.layout()

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Get a dive (and select it for future use)
        middleLayout = divelogScanLayout.itemAt(1).widget().layout()
        dive_tree = middleLayout.itemAt(1).widget()
        dive_item = dive_tree.topLevelItem(0)
        dive_tree.setCurrentItem(dive_item)

        # Get a picture element
        picture_grid = middleLayout.itemAt(0).widget()
        picture_container = picture_grid.layout().itemAtPosition(1, 0).widget()
        picture = picture_container.layout().itemAt(0).widget()
        error = picture_container.layout().itemAt(2).widget()

        # Drag a dive to the image
        drop_event = self.drag_drop(dive_tree, picture)
        picture_container.dropEvent(drop_event)

        # Trigger the validation
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        validate = bottomLayout.itemAt(4).widget()
        qtbot.mouseClick(validate, Qt.LeftButton)

        # Check results
        assert (
            error.text() == "Could not save 2022-04-09 16h45 - Carnet.jpg"
        ), "Dive error is OK"

    def test_divelogscans_validate_folder_not_selected(
        self, qtbot, pydive_db, pydive_divelog, pydive_mainwindow_empty_db
    ):
        pydive_mainwindow_empty_db.display_tab("DivelogScan")
        divelogScanLayout = pydive_mainwindow_empty_db.layout.currentWidget().layout()
        pydive_db.session.delete(pydive_db.storagelocations_get_target_scan_folder())
        pydive_db.session.commit()
        # Force screen refresh
        pydive_mainwindow_empty_db.display_tab("DivelogScan")

        # Load image file
        topLayout = divelogScanLayout.itemAt(0).widget().layout()
        path_change = topLayout.itemAt(2).widget()
        path_change.pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Trigger the validation
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        validate = bottomLayout.itemAt(4).widget()
        qtbot.mouseClick(validate, Qt.LeftButton)

        # Check results
        bottomLayout = divelogScanLayout.itemAt(2).widget().layout()
        path_wrapper = bottomLayout.itemAt(1).widget()
        path_error_display = path_wrapper.layout().itemAt(1).widget()
        assert (
            path_error_display.text() == "Please choose a target folder"
        ), "Error text is OK"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
