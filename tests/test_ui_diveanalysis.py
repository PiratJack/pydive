import os
import sys
import pytest
import pyqtgraph
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.divelog
from controllers.widgets.basetreewidget import BaseTreeWidget
from controllers.widgets.iconbutton import IconButton


class TestUiDiveAnalysis:
    @pytest.fixture
    def pydive_dive_analysis(self, pydive_mainwindow, pydive_divelog):
        pydive_mainwindow.display_tab("DiveAnalysis")

        yield pydive_mainwindow.layout.currentWidget()

    @pytest.fixture
    def pydive_ui(self, pydive_mainwindow, pydive_dive_analysis):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return pydive_mainwindow

            # Overall elements
            if element == "layout":
                return pydive_dive_analysis.layout()

            # Left part: Error (if no file selected) + Display of pictures & dives
            elif element == "left_layout":
                return pydive_dive_analysis.layout().itemAt(0).widget().layout()
            elif element == "file_load_error":
                return get_ui("left_layout").itemAt(0).widget()
            elif element == "dive_tree":
                return get_ui("left_layout").itemAt(1).widget()
            elif element == "tree_dive_172":
                return get_ui("dive_tree").topLevelItem(0)
            elif element == "tree_dive_171":
                return get_ui("dive_tree").topLevelItem(1)
            elif element == "tree_trip_Bouillante":
                return get_ui("dive_tree").topLevelItem(2)

            # Right part: Right part: Graph display & Export button
            elif element == "right_layout":
                return pydive_dive_analysis.layout().itemAt(1).widget().layout()
            elif element == "dive_graph":
                return get_ui("right_layout").itemAt(0).widget()
            elif element == "buttonbox":
                return get_ui("right_layout").itemAt(1).widget()
            elif element == "add_region":
                return get_ui("buttonbox").layout().itemAt(0).widget()
            elif element == "remove_region":
                return get_ui("buttonbox").layout().itemAt(1).widget()
            elif element == "export":
                return get_ui("buttonbox").layout().itemAt(3).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def click_tree_item(self, item, qtbot, pydive_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = pydive_ui("dive_tree").visualItemRect(item).topLeft()
        qtbot.mouseClick(
            pydive_ui("dive_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def test_diveanalysis_display(self, pydive_ui):
        # Check overall structure
        assert isinstance(pydive_ui("layout"), QtWidgets.QHBoxLayout), "Layout is OK"
        assert pydive_ui("layout").count() == 2, "Count of elements is OK"

        # Check left part
        part = "Left part - "
        assert isinstance(pydive_ui("left_layout"), QtWidgets.QVBoxLayout), (
            part + "Layout is OK"
        )
        assert pydive_ui("left_layout").count() == 2, part + "Count of elements is OK"

        assert isinstance(pydive_ui("file_load_error"), QtWidgets.QLabel), (
            part + "File load error is a QLabel"
        )

        assert isinstance(pydive_ui("dive_tree"), BaseTreeWidget), (
            part + "Dive tree is a BaseTreeWidget"
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

        # Check right part
        part = "Right part - "
        assert isinstance(pydive_ui("right_layout"), QtWidgets.QVBoxLayout), (
            part + "Layout is OK"
        )
        assert pydive_ui("right_layout").count() == 2, part + "Count of elements is OK"
        assert isinstance(pydive_ui("dive_graph"), pyqtgraph.PlotWidget), (
            part + "Dive Graph is a PlotWidget"
        )
        assert pydive_ui("buttonbox").layout().count() == 4, (
            part + "Count of elements is OK"
        )
        assert isinstance(pydive_ui("add_region"), IconButton), (
            part + "Add region is a IconButton"
        )
        assert isinstance(pydive_ui("remove_region"), IconButton), (
            part + "Add region is a IconButton"
        )
        assert isinstance(pydive_ui("export"), IconButton), (
            part + "Add region is a IconButton"
        )

    def test_diveanalysis_display_click_dive(self, pydive_ui, qtbot):
        # Click on dive
        self.click_tree_item(pydive_ui("tree_dive_172"), qtbot, pydive_ui)
        # Click a second time to clear everything (additional test)
        self.click_tree_item(pydive_ui("tree_dive_172"), qtbot, pydive_ui)

        # Check results
        items_displayed = len(pydive_ui("dive_graph").listDataItems())
        assert items_displayed == 4, "Graph displays information"

    def test_diveanalysis_display_click_trip(self, pydive_ui, qtbot):
        # Click on trip
        self.click_tree_item(pydive_ui("tree_trip_Bouillante"), qtbot, pydive_ui)

        # Check results
        items_displayed = len(pydive_ui("dive_graph").listDataItems())
        assert items_displayed == 1, "Graph displays nothing"

    def test_diveanalysis_display_click_trip_then_add_region(self, pydive_ui, qtbot):
        # Click on trip
        self.click_tree_item(pydive_ui("tree_trip_Bouillante"), qtbot, pydive_ui)

        # Click on add region
        original_count = len(pydive_ui("dive_graph").items())
        qtbot.mouseClick(pydive_ui("add_region"), Qt.LeftButton)

        # Check results
        new_count = len(pydive_ui("dive_graph").items())
        assert new_count == original_count, "No region is added"

    def test_diveanalysis_display_no_source_file(self, pydive_mainwindow_empty_db):
        pydive_mainwindow_empty_db.display_tab("DiveAnalysis")
        layout = pydive_mainwindow_empty_db.layout.currentWidget().layout()

        # Check error is displayed
        file_load_error = layout.itemAt(0).widget().layout().itemAt(0).widget()
        assert (
            file_load_error.text()
            == "Please select a divelog file in the settings screen"
        ), "Error message is displayed"

        # Check dive tree is empty
        dive_tree = layout.itemAt(0).widget().layout().itemAt(1).widget()
        assert dive_tree.topLevelItemCount() == 0, "Dive tree is empty"

    def test_diveanalysis_add_remove_region(self, pydive_ui, qtbot, monkeypatch):
        # Click on first displayed dive & setup monkeypatch
        self.click_tree_item(pydive_ui("tree_dive_172"), qtbot, pydive_ui)
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getMultiLineText", lambda *args: ("Peter", True)
        )

        # Click on add region
        original_count = len(pydive_ui("dive_graph").items())
        qtbot.mouseClick(pydive_ui("add_region"), Qt.LeftButton)
        # Doing this adds many different items in the graph (in the background)
        # Thus, the checks are not very precise

        # Check results
        new_count = len(pydive_ui("dive_graph").items())
        assert new_count > original_count, "New region is added"

        # Click on remove region
        qtbot.mouseClick(pydive_ui("remove_region"), Qt.LeftButton)

        # Check results
        final_count = len(pydive_ui("dive_graph").items())
        assert final_count == original_count, "New region is removed"

        # Remove a second time when there is nothing left to remove
        qtbot.mouseClick(pydive_ui("remove_region"), Qt.LeftButton)

        # Check results
        final_count = len(pydive_ui("dive_graph").items())
        assert final_count == original_count, "New region is removed"

    def test_diveanalysis_add_region_change_dive(self, pydive_ui, qtbot, monkeypatch):
        # Click on first displayed dive & setup monkeypatch
        self.click_tree_item(pydive_ui("tree_dive_172"), qtbot, pydive_ui)
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getMultiLineText", lambda *args: ("Peter", True)
        )

        # Click on add region
        original_count = len(pydive_ui("dive_graph").items())
        qtbot.mouseClick(pydive_ui("add_region"), Qt.LeftButton)

        # Click on another dive
        self.click_tree_item(pydive_ui("tree_dive_171"), qtbot, pydive_ui)

        # Check results
        final_count = len(pydive_ui("dive_graph").items())
        assert final_count == original_count, "Regions have been clear as well"

    def test_diveanalysis_export(self, pydive_ui, qtbot):
        # Simulating the actual dialog is impossible (it's OS-provided)
        path = os.path.join(pytest.BASE_FOLDER, "export.png")
        pydive_ui("export").pathSelected.emit(path)

        # Check file has been created
        assert os.path.exists(path), "Export has been created"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
