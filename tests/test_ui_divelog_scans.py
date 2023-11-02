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
    def pydive_divelog_scans(self, pydive_mainwindow, pydive_divelog):
        pydive_mainwindow.display_tab("DivelogScan")

        yield pydive_mainwindow.layout.currentWidget()

    @pytest.fixture
    def pydive_ui(self, pydive_mainwindow, pydive_divelog_scans):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return pydive_mainwindow

            # Overall elements
            if element == "layout":
                return pydive_divelog_scans.layout()

            # Top part: source file
            elif element == "top_layout":
                return pydive_divelog_scans.layout().itemAt(0).widget().layout()
            elif element == "source_file_label":
                return get_ui("top_layout").itemAt(0).widget()
            elif element == "source_file_path":
                wrapper = get_ui("top_layout").itemAt(1).widget()
                return wrapper.layout().itemAt(0).widget()
            elif element == "source_file_error":
                wrapper = get_ui("top_layout").itemAt(1).widget()
                return wrapper.layout().itemAt(1).widget()
            elif element == "source_file_change":
                return get_ui("top_layout").itemAt(2).widget()

            # Middle part: display of all images
            elif element == "middle_layout":
                return pydive_divelog_scans.layout().itemAt(1).widget().layout()
            elif element == "picture_grid":
                return get_ui("middle_layout").itemAt(0).widget()
            elif element == "dive_tree":
                return get_ui("middle_layout").itemAt(1).widget()

            # Bottom part: Target folder & validate button
            elif element == "bottom_layout":
                return pydive_divelog_scans.layout().itemAt(2).widget().layout()
            elif element == "target_folder_label":
                return get_ui("bottom_layout").itemAt(0).widget()
            elif element == "target_folder_path":
                wrapper = get_ui("bottom_layout").itemAt(1).widget()
                return wrapper.layout().itemAt(0).widget()
            elif element == "target_folder_error":
                wrapper = get_ui("bottom_layout").itemAt(1).widget()
                return wrapper.layout().itemAt(1).widget()
            elif element == "target_folder_change":
                return get_ui("bottom_layout").itemAt(2).widget()
                # item 3 is a spacer
            elif element == "validate":
                return get_ui("bottom_layout").itemAt(4).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

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

    def test_divelogscans_display(self, pydive_ui):
        # Check overall structure
        assert isinstance(pydive_ui("layout"), QtWidgets.QVBoxLayout), "Layout is OK"
        assert pydive_ui("layout").count() == 3, "Count of elements is OK"

        # Check top part
        part = "Top part - "
        assert isinstance(pydive_ui("top_layout"), QtWidgets.QHBoxLayout), (
            part + "Layout is OK"
        )
        assert pydive_ui("top_layout").count() == 3, part + "Count of elements is OK"

        assert isinstance(pydive_ui("source_file_label"), QtWidgets.QLabel), (
            part + "Name is a QLabel"
        )
        assert pydive_ui("source_file_label").text() == "Divelog scan to split", (
            part + "Name text is OK"
        )

        assert isinstance(pydive_ui("source_file_path"), QtWidgets.QLineEdit), (
            part + "Path is a QLineEdit"
        )
        assert pydive_ui("source_file_path").text() == "", part + "Path text is OK"

        assert isinstance(pydive_ui("source_file_error"), QtWidgets.QLabel), (
            part + "Error is a QLabel"
        )
        assert pydive_ui("source_file_error").text() == "", part + "Error text is OK"
        assert isinstance(pydive_ui("source_file_change"), PathSelectButton), (
            part + "Path change is PathSelectButton"
        )
        assert pydive_ui("source_file_change").target_type == "file", (
            part + "Path change looks for files"
        )

        # Check middle part
        part = "Middle part - "
        assert isinstance(pydive_ui("middle_layout"), QtWidgets.QHBoxLayout), (
            part + "Layout is OK"
        )
        assert pydive_ui("middle_layout").count() == 2, part + "Count of elements is OK"
        assert isinstance(pydive_ui("picture_grid"), QtWidgets.QWidget), (
            part + "Picture grid is QWidget"
        )
        assert isinstance(pydive_ui("picture_grid").layout(), QtWidgets.QGridLayout), (
            part + "Picture grid layout OK"
        )
        # Details of picture grid layout are done in separate function
        part = "Middle part - Dive tree - "
        assert isinstance(pydive_ui("dive_tree"), QtWidgets.QTreeWidget), (
            part + "Is QTreeWidget"
        )
        assert pydive_ui("dive_tree").topLevelItemCount() == 8, (
            part + "Count of elements OK"
        )
        types = ["dive", "dive", "trip", "trip", "dive", "trip", "dive", "dive"]
        for i, expected_type in enumerate(types):
            tree_type = pydive_ui("dive_tree").topLevelItem(i).data(0, Qt.UserRole)
            if expected_type == "trip":
                assert isinstance(tree_type, models.divelog.DiveTrip), (
                    part + "Item type is OK"
                )
                assert pydive_ui("dive_tree").topLevelItem(i).childCount() > 0, (
                    part + "Item has children"
                )
            elif expected_type == "dive":
                assert isinstance(tree_type, models.divelog.Dive), (
                    part + "Item type is OK"
                )

        # Check bottom part
        part = "Bottom part - "
        assert isinstance(pydive_ui("bottom_layout"), QtWidgets.QHBoxLayout), (
            part + "Layout is OK"
        )
        assert pydive_ui("bottom_layout").count() == 5, part + "Count of elements is OK"
        assert isinstance(pydive_ui("target_folder_label"), QtWidgets.QLabel), (
            part + "Name is a QLabel"
        )
        assert pydive_ui("target_folder_label").text() == "Target scan folder", (
            part + "Name text is OK"
        )
        assert isinstance(pydive_ui("target_folder_path"), QtWidgets.QWidget), (
            part + "Wrapper exists"
        )
        assert isinstance(pydive_ui("target_folder_path"), QtWidgets.QLineEdit), (
            part + "Path is a QLineEdit"
        )
        assert pydive_ui("target_folder_path").text() == pytest.BASE_FOLDER, (
            part + "Path text is OK"
        )
        assert isinstance(pydive_ui("target_folder_error"), QtWidgets.QLabel), (
            part + "Error is a QLabel"
        )
        assert pydive_ui("target_folder_error").text() == "", part + "Error text is OK"
        assert isinstance(pydive_ui("target_folder_change"), PathSelectButton), (
            part + "Path change is PathSelectButton"
        )
        assert pydive_ui("target_folder_change").target_type == "folder", (
            part + "Path change looks for folders"
        )
        assert isinstance(pydive_ui("validate"), QtWidgets.QPushButton), (
            part + "Validate is a QPushButton"
        )
        assert pydive_ui("validate").text() == "Validate", part + "Validate text is OK"

    def test_divelogscans_display_no_target_folder(self, pydive_mainwindow_empty_db):
        pydive_mainwindow_empty_db.display_tab("DivelogScan")
        divelogScanLayout = pydive_mainwindow_empty_db.layout.currentWidget().layout()

        # Check dive tree is empty
        part = "Middle part - Dive tree - "
        dive_tree = divelogScanLayout.itemAt(1).widget().layout().itemAt(1).widget()
        assert dive_tree.topLevelItemCount() == 0, part + "Count OK"

    def test_divelogscans_load_picture(self, pydive_ui):
        # Load image file
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        # Force reload of the same info (to check if it handles it well)
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)

        # Check overall display
        assert (
            pydive_ui("picture_grid").layout().columnCount() == 2
        ), "Picture grid - Column count OK"
        assert (
            pydive_ui("picture_grid").layout().rowCount() == 2
        ), "Picture grid - Row count OK"

        # Check one of the images
        part = "Picture container - "
        container = pydive_ui("picture_grid").layout().itemAtPosition(1, 0).widget()
        container_layout = container.layout()
        picture = container_layout.itemAt(0).widget()
        label = container_layout.itemAt(1).widget()
        error = container_layout.itemAt(2).widget()
        assert isinstance(container, QtWidgets.QWidget), part + "Is QWidget"
        assert isinstance(container_layout, QtWidgets.QVBoxLayout), part + "Layout OK"
        assert container_layout.count() == 3, part + "Element count OK"
        assert isinstance(picture, QtWidgets.QLabel), part + "Picture widget OK"
        assert picture.text() == "", part + "Picture has no text"
        assert isinstance(label, QtWidgets.QLabel), part + "Error widget OK"
        assert label.text() == "", part + "Error has no text"
        assert isinstance(error, QtWidgets.QLabel), part + "Error widget OK"
        assert error.text() == "", part + "Error has no text"

    def test_divelogscans_load_picture_error(self, pydive_ui):
        # Load image file, then non-image file
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_FILE)
        # Check error display
        assert (
            pydive_ui("source_file_error").text() == "Source file could not be read"
        ), "Error text is OK"

        # Load coorrect image file, check error disappears
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        # Check error display
        assert pydive_ui("source_file_error").text() == ""

    def test_divelogscans_link_picture_dive(self, pydive_ui):
        # Load image file, choose a dive
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        pydive_ui("dive_tree").setCurrentItem(pydive_ui("dive_tree").topLevelItem(0))

        # Get a picture element
        container = pydive_ui("picture_grid").layout().itemAtPosition(1, 0).widget()
        picture = container.layout().itemAt(0).widget()

        # Simulate drag / drop of the dive to the picture (by direct call to dropEvent)
        # Drag and drop can't be tested (thanks to bug QTBUG-5232) so this is a workaround
        drop_event = self.drag_drop(pydive_ui("dive_tree"), picture)
        container.dropEvent(drop_event)

        # Check results
        label = container.layout().itemAt(1).widget()
        error = container.layout().itemAt(2).widget()
        assert label.text() == "*Dive 172 on 2022-04-09 16:45:55", "Dive data is OK"
        assert error.text() == "", "Dive error is empty"

    def test_divelogscans_choose_target(self, pydive_ui):
        pydive_ui("target_folder_change").pathSelected.emit(pytest.BASE_FOLDER)
        assert (
            pydive_ui("target_folder_path").text() == pytest.BASE_FOLDER
        ), "Path display updated"

    def test_divelogscans_validate(self, pydive_ui, qtbot):
        # Load image file, assign dive to image & validate
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        pydive_ui("dive_tree").setCurrentItem(pydive_ui("dive_tree").topLevelItem(0))

        container = pydive_ui("picture_grid").layout().itemAtPosition(1, 0).widget()
        picture = container.layout().itemAt(0).widget()
        drop_event = self.drag_drop(pydive_ui("dive_tree"), picture)
        container.dropEvent(drop_event)

        qtbot.mouseClick(pydive_ui("validate"), Qt.LeftButton)

        # Check results
        new_file_path = os.path.join(
            pytest.BASE_FOLDER, "2022-04-09 16h45 - Carnet.jpg"
        )
        label = container.layout().itemAt(1).widget()
        error = container.layout().itemAt(2).widget()
        assert label.text() == "Dive 172 on 2022-04-09 16:45:55", "Dive data is OK"
        assert error.text() == "", "Dive error is empty"
        assert os.path.exists(new_file_path), "Split image saved"

    def test_divelogscans_validate_file_exists(self, pydive_ui, qtbot):
        # Load image file, assign dive to image & validate
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        pydive_ui("dive_tree").setCurrentItem(pydive_ui("dive_tree").topLevelItem(0))

        container = pydive_ui("picture_grid").layout().itemAtPosition(1, 0).widget()
        picture = container.layout().itemAt(0).widget()
        drop_event = self.drag_drop(pydive_ui("dive_tree"), picture)
        container.dropEvent(drop_event)

        qtbot.mouseClick(pydive_ui("validate"), Qt.LeftButton)
        # Trigger the validation a second time, so that the target file already exists
        qtbot.mouseClick(pydive_ui("validate"), Qt.LeftButton)

        # Check results
        error = container.layout().itemAt(2).widget()
        assert (
            error.text() == "File 2022-04-09 16h45 - Carnet.jpg already exists"
        ), "Dive error is OK"

    def test_divelogscans_validate_folder_does_not_exist(
        self, pydive_db, pydive_ui, qtbot
    ):
        existing_location = pydive_db.storagelocations_get_target_scan_folder()
        existing_location.path = os.path.join(pytest.BASE_FOLDER, "Inexistant")
        pydive_db.session.add(existing_location)
        pydive_db.session.commit()
        # Force screen refresh
        pydive_ui("mainwindow").display_tab("DivelogScan")

        # Load image file, assign dive to image & validate
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        pydive_ui("dive_tree").setCurrentItem(pydive_ui("dive_tree").topLevelItem(0))

        container = pydive_ui("picture_grid").layout().itemAtPosition(1, 0).widget()
        picture = container.layout().itemAt(0).widget()
        drop_event = self.drag_drop(pydive_ui("dive_tree"), picture)
        container.dropEvent(drop_event)

        qtbot.mouseClick(pydive_ui("validate"), Qt.LeftButton)

        # Check results
        error = container.layout().itemAt(2).widget()
        assert (
            error.text() == "Could not save 2022-04-09 16h45 - Carnet.jpg"
        ), "Dive error is OK"

    def test_divelogscans_validate_folder_not_selected(
        self, qtbot, pydive_db, pydive_divelog, pydive_ui
    ):
        # Delete existing folder
        pydive_db.session.delete(pydive_db.storagelocations_get_target_scan_folder())
        pydive_db.session.commit()
        # Force screen refresh
        pydive_ui("mainwindow").display_tab("DivelogScan")

        # Load image file & trigger validation
        pydive_ui("source_file_change").pathSelected.emit(pytest.DIVELOG_SCAN_IMAGE)
        qtbot.mouseClick(pydive_ui("validate"), Qt.LeftButton)

        # Check results
        assert (
            pydive_ui("target_folder_error").text() == "Please choose a target folder"
        ), "Error text is OK"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
