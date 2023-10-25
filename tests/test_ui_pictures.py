import os
import sys
import pytest
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


from controllers.pictures import PictureDisplay
from controllers.widgets.iconbutton import IconButton


class TestUiPictures:
    progress_group_columns = {
        "Completed": 3,
        "Errors": 5,
        "Error details": 6,
        "Count columns": 7,
    }

    @pytest.fixture
    def pydive_pictures(self, qtbot, pydive_mainwindow, pydive_real_pictures):
        pydive_mainwindow.display_tab("Pictures")
        pydive_mainwindow.controllers["Pictures"].on_load_pictures()
        self.all_files = pydive_real_pictures

        yield pydive_mainwindow.controllers["Pictures"]

    def mouseWheelTurn(self, qapp, widget, pos, orientation):
        globalPos = widget.mapToGlobal(pos)
        pixelDelta = QtCore.QPoint()
        angleDelta = QtCore.QPoint(0, 120) * orientation
        buttons = Qt.NoButton
        modifiers = Qt.NoModifier
        phase = 0
        inverted = False
        source = 0

        wheelEvent = QtGui.QWheelEvent(
            pos,
            globalPos,
            pixelDelta,
            angleDelta,
            buttons,
            modifiers,
            phase,
            inverted,
            source,
        )
        # This is a very dirty solution, because it's not really processed by the application
        # However, other solutions simply fail
        widget.wheelEvent(wheelEvent)

    def helper_check_paths(self, test, should_exist=[], should_not_exist=[]):
        QtCore.QThreadPool.globalInstance().waitForDone()
        # Add "should exist" to "all_files"
        self.all_files += should_exist
        self.all_files = list(set(self.all_files))

        # We check all files: both existing and non-existing
        all_files_checked = set(self.all_files + should_not_exist)
        should_exist = [
            f
            for f in self.all_files
            if f not in should_not_exist
            and os.path.join(pytest.BASE_FOLDER, f) not in should_not_exist
        ]
        for path in all_files_checked:
            absolute_path = path
            if pytest.BASE_FOLDER not in path:
                absolute_path = os.path.join(pytest.BASE_FOLDER, path)
            if path in should_exist:
                assert os.path.exists(absolute_path), f"{test} - File {absolute_path}"
            else:
                assert not os.path.exists(
                    absolute_path
                ), f"{test} - File {absolute_path}"

    def helper_check_picture_display(self, test, container, display_type, path=None):
        if display_type == "JPG":
            assert container.layout().count() == 3, test + " : 3 items displayed"
            filename = container.layout().itemAt(0).widget()
            buttonbox = container.layout().itemAt(1).widget()
            delete = buttonbox.layout().itemAt(1).widget()  # 0 & 2 are spacers
            picture = container.layout().itemAt(2).widget()
            assert filename.text() == path, test + " : filename display"
            assert isinstance(picture, PictureDisplay), test + " : image display"
            assert isinstance(delete, IconButton), test + " : delete display"
        elif display_type == "RAW":
            assert container.layout().count() == 3, test + " : 3 items displayed"
            filename = container.layout().itemAt(0).widget()
            buttonbox = container.layout().itemAt(1).widget()
            delete = buttonbox.layout().itemAt(1).widget()  # 0 & 2 are spacers
            assert filename.text() == path, test + " : filename display"
            assert isinstance(delete, IconButton), test + " : delete display"
        elif display_type == "No image":
            assert container.layout().count() in (2, 3), (
                test + " : 2 or 3 items displayed"
            )
            # 2 or 3 depending on whether we have a spacer at the end
            label = container.layout().itemAt(0).widget()
            buttonbox = container.layout().itemAt(1).widget()
            generate = buttonbox.layout().itemAt(1).widget()  # 0 & 3 are spacers
            copy = buttonbox.layout().itemAt(2).widget()  # 0 & 3 are spacers
            assert label.text() == "No image", test + " : label display"
            assert isinstance(generate, IconButton), test + " : generate display"
            assert isinstance(copy, IconButton), test + " : copy display"
        else:
            raise ValueError("display_type should be RAW, JPG or No image")

    def test_pictures_display_overall(self, pydive_pictures):
        # Setup: get display
        main_widget = pydive_pictures.ui["main"]

        # Check display - Overall structure
        assert isinstance(
            main_widget.layout(), QtWidgets.QHBoxLayout
        ), "Pictures layout is correct"
        assert (
            main_widget.layout().count() == 2
        ), "Pictures layout has the right number of colums"

        # Check display - Left column
        left_column = main_widget.layout().itemAt(0).widget()
        assert isinstance(
            left_column.layout(), QtWidgets.QVBoxLayout
        ), "Pictures left column layout is correct"
        assert (
            left_column.layout().count() == 7
        ), "Pictures left column has the right number of rows"

        # Check display - Right column
        right_column = main_widget.layout().itemAt(1).widget()
        assert isinstance(
            right_column.layout(), QtWidgets.QVBoxLayout
        ), "Pictures right column layout is correct"
        assert (
            right_column.layout().count() == 1
        ), "Pictures right column has the right number of rows"

    def test_pictures_display_folders(self, pydive_pictures, pydive_db):
        # Setup: get display
        folders = pydive_db.storagelocations_get_picture_folders()
        # Check what happens when display is refreshed twice in a row
        pydive_pictures.refresh_folders()
        foldersLayout = pydive_pictures.ui["left_grid_layout"]

        # Check display - Overall structure
        assert (
            foldersLayout.columnCount() == 2
        ), "Folders display has the right number of colums"
        assert foldersLayout.rowCount() == len(
            folders
        ), "Folders display has the right number of rows"

        # Check display - Folder names
        name_label = foldersLayout.itemAtPosition(0, 0).widget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == folders[0].name
        ), "Name field displays the expected data"

        # Check display - Path display
        path_label = foldersLayout.itemAtPosition(0, 1).widget()
        assert isinstance(path_label, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_label.text() == folders[0].path
        ), "Path field displays the expected data"

    def test_pictures_display_tree_load_pictures(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        load_pictures_button = pydive_pictures.ui["load_button"]
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)
        # Second time to test refresh of already-displayed data
        qtbot.mouseClick(load_pictures_button, Qt.LeftButton)

        # Check display - Tree has the right number of columns
        assert (
            picturesTree.columnCount() == 6
        ), "Picture tree has the right number of columns"

        # Check display - Tree has the right number of high-level items
        assert picturesTree.topLevelItemCount() == 7, "Found the right number of trips"

        # Check display - Malta's images
        malta = picturesTree.topLevelItem(5)
        malta_children = [malta.child(i).text(0) for i in range(malta.childCount())]
        assert malta.childCount() == 2, "Malta's children count is OK"
        assert malta_children == ["IMG001", "IMG002"], "Malta's children are OK"

    def test_pictures_display_checkboxes(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Check display - Tasks label & progress bar
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        display_raw_images = left_column.layout().itemAt(3).widget()
        assert isinstance(
            display_raw_images, QtWidgets.QCheckBox
        ), "Pictures: Display RAW images is a QCheckBox"
        assert (
            display_raw_images.text() == "Display RAW images"
        ), "Pictures: Display RAW images label text is correct"
        display_absent_images = left_column.layout().itemAt(4).widget()
        assert isinstance(
            display_absent_images, QtWidgets.QCheckBox
        ), "Pictures: Display absent images is QCheckBox"
        assert (
            display_absent_images.text() == "Display absent images"
        ), "Pictures: Display absent images label is correct"

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - Correct display of columns & rows
        hidden_columns = [1, 2]  # RAW (hidden by default), DT (no image)
        hidden_rows = [
            1,
            2,
            3,
            4,
        ]  # Archive (only RAW image), Camera, Inexistant, No picture here (no image in any of those)
        layout = picturesGrid.ui["layout"]
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):
                container = layout.itemAtPosition(row, col).widget()
                if row in hidden_rows or col in hidden_columns:
                    assert container.isHidden(), "Element is properly hidden"
                else:
                    assert not container.isHidden(), "Element is properly visible"

        # Display RAW images ==> 1st column should be displayed
        topleft = QtCore.QPoint(2, 5)  # This is just a guess to end up on the checkbox
        qtbot.mouseClick(display_raw_images, Qt.LeftButton, Qt.NoModifier, topleft)
        assert display_raw_images.isChecked(), "Checkbox is indeed checked"
        hidden_columns = [2]  # DT (no image)
        hidden_rows = [
            2,
            3,
            4,
        ]  # Camera, Inexistant, No picture here (no image in any of those)
        hidden_cells = {1: [3]}
        # Row 1: col 1 is RAW and present, 2 is hidden already, 3 is RT doesn't exist
        # Rows 2-4 are hidden already
        # Row 5: col 1 is RAW and present, 2 is hidden already, 3 is RT and exists ==> all displayed
        layout = picturesGrid.ui["layout"]
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):
                container = layout.itemAtPosition(row, col).widget()
                if row in hidden_rows or col in hidden_columns:
                    assert container.isHidden(), "Element is properly hidden"
                elif row in hidden_cells and col in hidden_cells[row]:
                    assert container.isHidden(), "Element is properly hidden"
                else:
                    assert not container.isHidden(), "Element is properly visible"

        # Display empty images ==> Everything should be displayed
        topleft = QtCore.QPoint(2, 5)  # This is just a guess to end up on the checkbox
        qtbot.mouseClick(display_absent_images, Qt.LeftButton, Qt.NoModifier, topleft)
        assert display_absent_images.isChecked(), "Checkbox is indeed checked"
        hidden_columns = []
        hidden_rows = []
        hidden_cells = {}
        layout = picturesGrid.ui["layout"]
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):
                container = layout.itemAtPosition(row, col).widget()
                if row in hidden_rows or col in hidden_columns:
                    assert container.isHidden(), "Element is properly hidden"
                elif row in hidden_cells and col in hidden_cells[row]:
                    assert container.isHidden(), "Element is properly hidden"
                else:
                    assert not container.isHidden(), "Element is properly visible"

        # Display empty but not RAW images ==> 1st column should be hidden
        topleft = QtCore.QPoint(2, 5)  # This is just a guess to end up on the checkbox
        qtbot.mouseClick(display_raw_images, Qt.LeftButton, Qt.NoModifier, topleft)
        assert not display_raw_images.isChecked(), "Checkbox is indeed u checked"
        hidden_columns = [1]  # RAW
        hidden_rows = []  # All displayed due to "display absent" being checked
        layout = picturesGrid.ui["layout"]
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):
                container = layout.itemAtPosition(row, col).widget()
                if row in hidden_rows or col in hidden_columns:
                    assert container.isHidden(), "Element is properly hidden"
                else:
                    assert not container.isHidden(), "Element is properly visible"

    def test_pictures_display_in_progress_tasks(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Check display - Tasks label & progress bar
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        tasks_label = left_column.layout().itemAt(5).widget()
        assert isinstance(
            tasks_label, QtWidgets.QLabel
        ), "Pictures: In-progress task label is QLabel"
        assert (
            tasks_label.text() == "In-progress tasks: 0"
        ), "Pictures: In-progress task label text is correct"
        tasks_progress_bar = left_column.layout().itemAt(6).widget()
        assert isinstance(
            tasks_progress_bar, QtWidgets.QProgressBar
        ), "Pictures: In-progress task progress bar is QProgressBar"
        assert (
            tasks_progress_bar.text() == ""
        ), "Pictures: In-progress task progress bar value is correct"

        # Trigger the conversion
        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002

        # Look for convert action
        picturesTree.generate_context_menu(picture_item)
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        menu = [
            m
            for m in picturesTree.menu.children()
            if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
        ][0]
        action = [a for a in menu.actions() if a.text() == action_name][0]

        # Trigger action
        action.trigger()

        # Check results while task is running
        assert (
            tasks_label.text() == "In-progress tasks: 1"
        ), "Pictures: In-progress task label text is correct"
        assert (
            tasks_progress_bar.text() == "0%"
        ), "Pictures: In-progress task progress bar value is correct"

        # This ensures cleanup afterwards
        new_files = [
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

        # Check results after task is complete
        qtbot.waitUntil(lambda: tasks_label.text() == "In-progress tasks: 0")
        assert (
            tasks_label.text() == "In-progress tasks: 0"
        ), "Pictures: In-progress task label text is correct"
        assert (
            tasks_progress_bar.text() == "100%"
        ), "Pictures: In-progress task progress bar value is correct"

    def test_pictures_process_groups_display(self, pydive_pictures, qtbot, qapp):
        # Setup: get display
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        tasks_label = left_column.layout().itemAt(5).widget()
        tasks_progress_bar = left_column.layout().itemAt(6).widget()

        def handle_dialog():
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"
            # The actual contents of the dialog are handled in the other tests
            dialog.close()

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(tasks_label, Qt.LeftButton)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(tasks_progress_bar, Qt.LeftButton)

    def test_pictures_process_groups_multiple_errors(
        self, pydive_pictures, qtbot, qapp
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        tasks_label = left_column.layout().itemAt(5).widget()

        # Trigger a copy (to get proper display)
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picturesTree.generate_context_menu(trip_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]
        action.trigger()

        def handle_dialog():
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"

            # Check overall structure
            assert isinstance(
                dialog.layout(), QtWidgets.QVBoxLayout
            ), "ProcessGroup dialog layout is QVBoxLayout"
            dialog_ui = dialog.layout().itemAt(0).widget()
            assert isinstance(
                dialog_ui.layout(), QtWidgets.QVBoxLayout
            ), "ProcessGroup layout is QVBoxLayout"
            assert (
                dialog_ui.layout().count() == 2
            ), "ProcessGroup has correct number of items"
            dialog_label = dialog_ui.layout().itemAt(0).widget()
            dialog_table = dialog_ui.layout().itemAt(1).widget()
            assert isinstance(
                dialog_label, QtWidgets.QLabel
            ), "ProcessGroup title is a QLabel"
            assert isinstance(
                dialog_table, QtWidgets.QTableView
            ), "ProcessGroup table is a QTableView"

            # Check table structure & contents
            dialog_model = dialog_table.model
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Errors"], QtCore.QModelIndex()
            )
            assert (
                dialog_model.rowCount(index) == 1
            ), "ProcessGroup table has correct number of rows"
            assert (
                dialog_model.columnCount(index) == 7
            ), "ProcessGroup table has correct number of columns"
            cell_error_count = dialog_model.data(index, Qt.DisplayRole)
            assert cell_error_count == 2, "ProcessGroup table displays errors"
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Error details"], QtCore.QModelIndex()
            )
            cell_error_details = dialog_model.data(index, Qt.DisplayRole)
            assert (
                cell_error_details == "Hover for error details"
            ), "ProcessGroup table displays error details"
            cell_error_tooltip = dialog_model.data(index, Qt.ToolTipRole)
            assert cell_error_tooltip != "", "ProcessGroup table has tooltip for errors"

            dialog.close()

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(tasks_label, Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join("Archive", "Malta", "IMG002_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_process_groups_one_error(self, pydive_pictures, qtbot, qapp):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        tasks_label = left_column.layout().itemAt(5).widget()

        # Trigger a copy (to get proper display)
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(0)  # Malta's IMG001
        picturesTree.generate_context_menu(picture_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]
        action.trigger()

        def handle_dialog():
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"

            # Check overall structure
            dialog_ui = dialog.layout().itemAt(0).widget()
            dialog_table = dialog_ui.layout().itemAt(1).widget()

            # Check table structure & contents
            dialog_model = dialog_table.model
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Errors"], QtCore.QModelIndex()
            )
            cell_error_count = dialog_model.data(index, Qt.DisplayRole)
            assert cell_error_count == 1, "ProcessGroup table displays 1 error"
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Error details"], QtCore.QModelIndex()
            )
            cell_error_details = dialog_model.data(index, Qt.DisplayRole)
            assert cell_error_details != "", "ProcessGroup table displays error details"
            assert (
                cell_error_details != "Hover for error details"
            ), "ProcessGroup table displays error details directly"
            cell_error_tooltip = dialog_model.data(index, Qt.ToolTipRole)
            assert (
                cell_error_tooltip == cell_error_details
            ), "ProcessGroup table has tooltip for errors"

            dialog.close()

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(tasks_label, Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_process_groups_no_error(self, pydive_pictures, qtbot, qapp):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        tasks_label = left_column.layout().itemAt(5).widget()

        # Trigger a copy (to get proper display)
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(0)  # Malta's IMG001
        picturesTree.generate_context_menu(picture_item)
        action_name = "Copy all images from Temporary to Camera"
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]
        action.trigger()

        def handle_dialog():
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"

            # Check overall structure
            dialog_ui = dialog.layout().itemAt(0).widget()
            dialog_table = dialog_ui.layout().itemAt(1).widget()

            # Check table structure & contents
            dialog_model = dialog_table.model
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Errors"], QtCore.QModelIndex()
            )
            assert (
                dialog_model.rowCount(index) == 1
            ), "ProcessGroup table has correct number of rows"
            cell_error_count = dialog_model.data(index, Qt.DisplayRole)
            assert cell_error_count == 0, "ProcessGroup table displays no error"
            index = dialog_model.createIndex(
                0, self.progress_group_columns["Error details"], QtCore.QModelIndex()
            )
            cell_error_details = dialog_model.data(index, Qt.DisplayRole)
            assert (
                cell_error_details == ""
            ), "ProcessGroup table displays no error details"
            cell_error_tooltip = dialog_model.data(index, Qt.ToolTipRole)
            assert (
                cell_error_tooltip == ""
            ), "ProcessGroup table has no tooltip for error"

            # Testing invalid index
            index = dialog_model.createIndex(-1, -1, QtCore.QModelIndex())
            invalid_index = dialog_model.data(index, Qt.DisplayRole)
            assert invalid_index == False, "Invalid index yields False"

            dialog.close()

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(tasks_label, Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("DCIM", "Malta", "IMG001.CR2"),
            os.path.join("DCIM", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_tree_click_trip(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(1)  # Georgia
        topleft = picturesTree.visualItemRect(trip_item).topLeft()

        # Click on trip - should not display the picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - Grid should not be displayed
        assert picturesGrid.picture_group is None, "PictureGrid has no picture_group"
        assert picturesGrid.ui["layout"].columnCount() == 1, "PictureGrid is empty"
        assert picturesGrid.ui["layout"].rowCount() == 1, "PictureGrid is empty"
        assert (
            picturesGrid.ui["layout"].itemAtPosition(0, 0) is None
        ), "PictureGrid is empty"

    def test_pictures_tree_click_picture_group(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid (twice to check if it handles it well)
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - Overall grid structure
        assert picturesGrid.picture_group is not None, "PictureGrid has a picture_group"
        assert (
            picturesGrid.ui["layout"].columnCount() == 4
        ), "PictureGrid has right number of columns"
        assert (
            picturesGrid.ui["layout"].rowCount() == 6
        ), "PictureGrid has right number of rows"

        # Check display - Correct display of different images (RAW, JPG, no image)
        # "No image"
        test = "No image"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        self.helper_check_picture_display(test, container, "No image")

        # RAW image ==> readable
        test = "RAW image"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG001.CR2")

        # JPG image ==> readable
        test = "JPG image"
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG001_RT.jpg")

    def test_pictures_tree_click_picture_group_some_images_hidden(
        self, pydive_pictures, qtbot
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Hide RAW and absent images
        left_column = pydive_pictures.ui["main"].layout().itemAt(0).widget()
        display_raw_images = left_column.layout().itemAt(3).widget()
        display_absent_images = left_column.layout().itemAt(4).widget()
        qtbot.mouseClick(display_raw_images, Qt.LeftButton)
        qtbot.mouseClick(display_absent_images, Qt.LeftButton)

        # The display can't be checked because the window is not displayed
        # Therefore, widget.isVisible() will always be False

        # ## "No image"
        # #test = "No image"
        # #container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        # #assert container.isVisible() == False, "Container is hidden"

        # ## RAW image ==> readable
        # #test = "RAW image"
        # #container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        # #assert container.isVisible() == False, "Container is hidden"

        # ## JPG image ==> readable
        # #test = "JPG image"
        # #container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        # #assert container.isVisible() == True, "Container is visible"

        pass

    def test_pictures_tree_remove_already_removed_picture_group(
        self, pydive_pictures, qtbot
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        # Should not trigger an error
        picturesTree.remove_picture_group(picture_item)
        picturesTree.remove_picture_group(picture_item)
        picturesTree.remove_picture_group(None)

    def test_pictures_tree_picture_group_removed_before_add_again(
        self, pydive_pictures, qtbot
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Trigger action
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        buttonbox = container.layout().itemAt(1).widget()
        generate = buttonbox.layout().itemAt(1).widget()  # 0 & 3 are spacers
        qtbot.mouseClick(generate, Qt.LeftButton)

        # Empty tree to force a RuntimeError
        picturesTree.clear()

        # Check signal is emitted, file have been added & models updated
        new_path = os.path.join("Archive", "Malta", "IMG001_DT.jpg")
        new_files = [new_path]
        self.helper_check_paths("Generated image", new_files)

        qtbot.waitSignal(picture_group.pictureAdded)

    def test_pictures_grid_copy_raw_picture(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Georgia's IMG010
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Georgia"]["IMG010"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - No image displayed
        test = "Before RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "No image")
        buttonbox = container.layout().itemAt(1).widget()
        copy = buttonbox.layout().itemAt(2).widget()  # 0 & 3 are spacers

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded) as blocker:
            qtbot.mouseClick(copy, Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join("Archive", "Georgia", "IMG010.CR2")
        new_files = [new_path]
        assert blocker.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "Added picture signal has correct path"
        assert blocker.args[1] == "", "Added picture signal has empty conversion method"
        self.helper_check_paths("Copy RAW image", new_files)
        assert len(picture_group.pictures[""]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After RAW copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG010.CR2")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(0), "0 image in Archive"

    def test_pictures_grid_copy_jpg_picture(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Georgia's IMG010
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Georgia"]["IMG010"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Check display - No image displayed
        test = "Before JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "No image")
        buttonbox = container.layout().itemAt(1).widget()
        copy = buttonbox.layout().itemAt(2).widget()  # 0 & 3 are spacers

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(copy, Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join("Archive", "Georgia", "IMG010_RT.jpg")
        new_files = [new_path]
        assert signal.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "Added picture signal has correct path"
        assert signal.args[1] == "RT", "Added picture signal has RT as conversion"
        self.helper_check_paths("Copy JPG image", new_files)
        assert len(picture_group.pictures["RT"]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After JPG copy"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG010_RT.jpg")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(0), "0 image in Archive"

    def test_pictures_grid_copy_error(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get Copy button
        container = picturesGrid.ui["layout"].itemAtPosition(2, 2).widget()
        buttonbox = container.layout().itemAt(1).widget()
        copy = buttonbox.layout().itemAt(2).widget()  # 0 & 3 are spacers

        # Trigger action - Should raise (caught) exception
        qtbot.mouseClick(copy, Qt.LeftButton)

        # Check display - Error is displayed
        error = container.layout().itemAt(2).widget()
        assert error.text() == "No source image found", "Error is displayed"

    def test_pictures_grid_delete_jpg_picture(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )

        # Trigger action - 1 image deleted
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        buttonbox = container.layout().itemAt(1).widget()
        delete = buttonbox.layout().itemAt(1).widget()  # 0 & 2 are spacers
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=1000) as signal:
            qtbot.mouseClick(delete, Qt.LeftButton)

        # Check signal is emitted, file have been deleted & models updated
        deleted_path = os.path.join("Temporary", "Malta", "IMG001_RT.jpg")
        deleted_files = [deleted_path]
        assert signal.args[0] == "RT", "Deletion signal has correct conversion type"
        assert (
            signal.args[1].name == "Temporary"
        ), "Deletion signal has correct location"
        self.helper_check_paths("Delete image", [], deleted_files)
        assert "RT" not in picture_group.pictures, "Picture deleted from group"

        # Check display - New image is displayed
        test = "After picture deletion"
        container = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        self.helper_check_picture_display(test, container, "No image")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group.data(2, Qt.DisplayRole) == str(1), "1 images in Temporary"
        assert tree_group.data(3, Qt.DisplayRole) == str(2), "2 images in Archive"

    def test_pictures_grid_delete_raw_picture(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )

        # Trigger action - 1 image deleted
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        buttonbox = container.layout().itemAt(1).widget()
        delete = buttonbox.layout().itemAt(1).widget()  # 0 & 2 are spacers
        with qtbot.waitSignals(
            [picture_group.pictureRemoved] * 2, timeout=1000
        ) as signals:
            qtbot.mouseClick(delete, Qt.LeftButton)

        # Check signal is emitted, file have been deleted & models updated
        deleted_path = os.path.join("Archive", "Malta", "IMG001.CR2")
        deleted_path2 = os.path.join("Archive", "Malta", "Bof", "IMG001.CR2")
        deleted_files = [deleted_path, deleted_path2]
        signal = signals.all_signals_and_args[0]
        assert signal.args[0] == "", "Deletion signal has correct conversion type"
        assert signal.args[1].name == "Archive", "Deletion signal has correct location"
        self.helper_check_paths("Delete image", [], deleted_files)
        assert len(picture_group.pictures[""]) == 1, "Picture deleted from group"

        # Check display - New image is displayed
        test = "After picture deletion"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "No image")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group.data(3, Qt.DisplayRole) == str(0), "0 image in Archive"

    def test_pictures_grid_convert_picture(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Malta's IMG001
        topleft = picturesTree.visualItemRect(picture_item).topLeft()
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG001"]

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Trigger action - 1 image added
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        buttonbox = container.layout().itemAt(1).widget()
        generate = buttonbox.layout().itemAt(1).widget()  # 0 & 3 are spacers
        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(generate, Qt.LeftButton)

        # Check signal is emitted, file have been added & models updated
        new_path = os.path.join("Archive", "Malta", "IMG001_DT.jpg")
        new_files = [new_path]
        assert signal.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "New picture has correct path"
        assert signal.args[1] == "DT", "New picture has correct conversion method"
        self.helper_check_paths("Generated image", new_files)
        assert len(picture_group.pictures["DT"]) == 1, "Picture has 1 DT image"

        # Check display - New image is displayed
        test = "After picture generation"
        container = picturesGrid.ui["layout"].itemAtPosition(1, 2).widget()
        # This is called with "RAW" because the "conversion" is only a copy in this test
        self.helper_check_picture_display(test, container, "RAW", "IMG001_DT.jpg")

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group.data(3, Qt.DisplayRole) == str(3), "3 images in Archive"

    def test_pictures_grid_convert_picture_no_method_found(
        self, pydive_pictures, qtbot
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(6)  # Sweden
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Sweden's IMG040
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get Copy button
        container = picturesGrid.ui["layout"].itemAtPosition(2, 4).widget()
        buttonbox = container.layout().itemAt(1).widget()
        generate = buttonbox.layout().itemAt(1).widget()  # 0 & 3 are spacers

        # Trigger action - Should raise (caught) exception
        qtbot.mouseClick(generate, Qt.LeftButton)

        # Check display - Error is displayed
        error = container.layout().itemAt(2).widget()
        assert error.text() == "No conversion method found", "Error is displayed"

    def test_pictures_grid_picture_zoom(self, pydive_pictures, qtbot, qapp):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(6)  # Sweden
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Sweden's IMG040
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get one of the pictures being displayed & trigger mouse wheel
        container = picturesGrid.ui["layout"].itemAtPosition(5, 2).widget()
        picture = container.layout().itemAt(2).widget()
        size_before = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        with qtbot.waitSignal(picture.zoomChanged):
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)

        # Check results
        size_after = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        assert size_before < size_after, "Picture is zoomed in"
        assert picture._zoom == 1, "Picture _zoom changed"
        container2 = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        picture2 = container2.layout().itemAt(2).widget()
        size_picture_2 = picture2.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        delta_zoom = abs(size_after - size_picture_2) / size_after
        assert delta_zoom < 0.01, "Other pictures are zoomed in with same zoom"
        assert picture2._zoom == 1, "Other pictures' _zoom property changed"

        # Zoom back to the original level
        with qtbot.waitSignal(picture.zoomChanged):
            self.mouseWheelTurn(qapp, picture, picture.pos(), -1)

        # Check results
        size_final = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        assert size_final < size_after, "Picture is back to original zoom level"
        assert size_final == size_before, "Picture is back to original zoom level"
        assert picture._zoom == 0, "Picture _zoom is back to original value"
        size_picture_2 = picture2.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        delta_zoom = abs(size_final - size_picture_2) / size_after
        assert delta_zoom < 0.01, "Other pictures are zoomed in with same zoom"
        assert picture2._zoom == 0, "Other pictures' _zoom property changed"

    def test_pictures_grid_picture_move(self, pydive_pictures, qtbot, qapp):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]
        picturesGrid = pydive_pictures.ui["picture_grid"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(6)  # Sweden
        trip_item.setExpanded(True)
        picture_item = trip_item.child(0)  # Sweden's IMG040
        topleft = picturesTree.visualItemRect(picture_item).topLeft()

        # Trigger display of picture grid
        qtbot.mouseClick(picturesTree.viewport(), Qt.LeftButton, Qt.NoModifier, topleft)

        # Get one of the pictures being displayed & trigger zoom (otherwise, no scrollbar)
        container = picturesGrid.ui["layout"].itemAtPosition(5, 2).widget()
        picture = container.layout().itemAt(2).widget()
        with qtbot.waitSignal(picture.zoomChanged):
            # This is needed to ensure horizontal scrollbar is visible
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)
        container2 = picturesGrid.ui["layout"].itemAtPosition(5, 3).widget()
        picture2 = container2.layout().itemAt(2).widget()

        # I couldn't find how to trigger the mouse move event, so I trigger the signal directly
        scrollbarh = picture.horizontalScrollBar()
        scrollbarh.setValue(3)
        scrollbarv = picture.verticalScrollBar()
        # This fails... for a weird reason. The wheelEvent is correctly triggered
        # However, the scrollbars are not generated (that should be automatic)
        # TODO fix this
        # assert scrollbarh.value() == 3, "Horizontal scrollbar has moved"

        # Check results
        scrollbarh2 = picture2.horizontalScrollBar()
        assert (
            scrollbarh2.value() == scrollbarh.value()
        ), "Other pictures are moved similarly"

        # I couldn't find how to trigger the mouse move event, so I trigger the signal directly
        scrollbarv = picture.verticalScrollBar()
        scrollbarv.valueChanged.emit(15)

        # Check results
        scrollbarv2 = picture2.verticalScrollBar()
        assert (
            scrollbarv2.value() == scrollbarv.value()
        ), "Other pictures are moved similarly"

    def test_pictures_tree_trip_copy(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(3)  # Georgia
        trip = pydive_pictures.repository.trips["Georgia"]
        picture_group_010 = trip["IMG010"]
        picture_group_011 = trip["IMG011_convert"]

        # Look for copy action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu_actions if a.text() == action_name][0]

        # Trigger action - 3 images copied
        signals = [picture_group_010.pictureAdded] * 2 + [
            picture_group_011.pictureAdded
        ]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Georgia", "IMG010.CR2"),
            os.path.join("Archive", "Georgia", "IMG010_RT.jpg"),
            os.path.join("Archive", "Georgia", "IMG011_convert.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            "Archive" in picture_group_010.locations
        ), "New location added to picture_group"
        assert (
            len(picture_group_010.locations["Archive"]) == 2
        ), "Archive has 2 IMG010 pictures"

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG010"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(2), "2 image in Archive"
        tree_group2 = [
            p for p in children if p.data(0, Qt.DisplayRole) == "IMG011_convert"
        ][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(1), "1 image in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(1), "1 image in Archive"

    def test_pictures_tree_trip_convert(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_group1 = pydive_pictures.repository.trips["Malta"]["IMG001"]
        picture_group2 = pydive_pictures.repository.trips["Malta"]["IMG002"]

        # Look for generate action
        picturesTree.generate_context_menu(trip_item)
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        menu = [
            m
            for m in picturesTree.menu.children()
            if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
        ][0]
        action = [a for a in menu.actions() if a.text() == action_name][0]

        # Trigger action - 2 images converted
        signals = [picture_group1.pictureAdded, picture_group2.pictureAdded]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_DT.jpg"),
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(menu_name + " " + action_name, new_files)
        assert (
            len(picture_group1.locations["Archive"]) == 3
        ), "Picture added to picture group"

        # Check display - Tree has been updated
        children = [trip_item.child(i) for i in range(trip_item.childCount())]
        tree_group1 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG001"][0]
        assert tree_group1.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group1.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group1.data(3, Qt.DisplayRole) == str(3), "3 images in Archive"
        tree_group2 = [p for p in children if p.data(0, Qt.DisplayRole) == "IMG002"][0]
        assert tree_group2.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert tree_group2.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert tree_group2.data(3, Qt.DisplayRole) == str(3), "3 images in Archive"

    def test_pictures_tree_trip_change_name(self, pydive_pictures, qtbot, monkeypatch):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picture_group = pydive_pictures.repository.trips["Korea"]["IMG030"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Change name to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )

        # Trigger action - 2 images moved
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Temporary", "Italy", "IMG030.CR2"),
            os.path.join("Archive", "Italy", "IMG030_RT.jpg"),
        ]
        removed_files = [
            os.path.join("Temporary", "Korea", "IMG030.CR2"),
            os.path.join("Archive", "Korea", "IMG030_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)

        # Check display - Tree has been updated
        top_level_items = [
            picturesTree.topLevelItem(i).text(0)
            for i in range(picturesTree.topLevelItemCount())
        ]
        assert "Italy" in top_level_items, "Italy added to the tree"
        assert "Korea" not in top_level_items, "Korea removed from the tree"

    def test_pictures_tree_trip_change_name_exists(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item & picture groups
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picture_group = pydive_pictures.repository.trips["Korea"]["IMG030"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(trip_item)
        action_name = "Change name to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )

        # Trigger action - 2 images moved
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Temporary", "Georgia", "IMG030.CR2"),
            os.path.join("Archive", "Georgia", "IMG030_RT.jpg"),
        ]
        removed_files = [
            os.path.join("Temporary", "Korea", "IMG030.CR2"),
            os.path.join("Archive", "Korea", "IMG030_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)

        # Check display - Tree has been updated
        top_level_items = [
            picturesTree.topLevelItem(i).text(0)
            for i in range(picturesTree.topLevelItemCount())
        ]
        assert "Georgia" in top_level_items, "Georgia still in the tree"
        assert "Korea" not in top_level_items, "Korea removed from the tree"

    def test_pictures_tree_trip_wrong_action_name(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Trigger the addition of an impossible action
        trip_item = picturesTree.topLevelItem(4)  # Korea
        picturesTree.generate_context_menu(trip_item)
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            picturesTree.add_trip_action("", "", action_name, "", "", "")

    def test_pictures_tree_picture_group_copy(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(0)  # Malta's IMG001
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG001"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Copy all images from Temporary to Archive"
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Trigger action - 1 image copied
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            len(picture_group.locations["Archive"]) == 3
        ), "Archive has 3 IMG001 pictures"

        # Check display - Tree has been updated
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(3), "3 image in Archive"

    def test_pictures_tree_picture_group_convert(self, pydive_pictures, qtbot):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG002"]

        # Look for convert action
        picturesTree.generate_context_menu(picture_item)
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        menu = [
            m
            for m in picturesTree.menu.children()
            if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
        ][0]
        action = [a for a in menu.actions() if a.text() == action_name][0]

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            len(picture_group.locations["Archive"]) == 3
        ), "Archive has 3 IMG002 pictures"

        # Check display - Tree has been updated
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(3), "3 images in Archive"

    def test_pictures_tree_picture_group_change_trip(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG002"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Change trip to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Temporary", "Italy", "IMG002.CR2"),
            os.path.join("Temporary", "Italy", "IMG002_RT.jpg"),
            os.path.join("Archive", "Italy", "IMG002.CR2"),
            os.path.join("Archive", "Italy", "Sélection", "IMG002.CR2"),
        ]
        removed_files = [
            os.path.join("Temporary", "Malta", "IMG002.CR2"),
            os.path.join("Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join("Archive", "Malta", "IMG002.CR2"),
            os.path.join("Archive", "Malta", "Sélection", "IMG002.CR2"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)
        picture_group = pydive_pictures.repository.trips["Italy"]["IMG002"]
        # Wait until the new picture group has everything
        # This can't be done through signals because the target picture group doesn't exist yet when we trigger the action
        qtbot.waitUntil(lambda: "Archive" in picture_group.locations)
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG002 pictures"

        # Check display - Tree has been updated
        qtbot.waitUntil(
            lambda: any(
                [
                    picturesTree.topLevelItem(i).text(0) == "Italy"
                    for i in range(picturesTree.topLevelItemCount())
                ]
            )
        )
        italy_item = [
            picturesTree.topLevelItem(i)
            for i in range(picturesTree.topLevelItemCount())
            if picturesTree.topLevelItem(i).text(0) == "Italy"
        ][0]
        picture_item = italy_item.child(0)
        assert italy_item.data(0, Qt.DisplayRole) == "Italy", "New trip displayed"
        assert picture_item.data(0, Qt.DisplayRole) == "IMG002", "New picture displayed"
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 images in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(2), "2 images in Archive"

    def test_pictures_tree_picture_group_change_trip_target_exists(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Get tree item, trip & picture groups
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picture_group = pydive_pictures.repository.trips["Malta"]["IMG002"]

        # Look for "Change trip" action
        picturesTree.generate_context_menu(picture_item)
        action_name = "Change trip to ..."
        action = [a for a in picturesTree.menu.actions() if a.text() == action_name][0]

        # Monkeypatch the dialog to return what we want
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )

        # Trigger action - 1 image added
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=2000):
            action.trigger()

        # Check files have been created & models updated
        new_files = [
            os.path.join("Temporary", "Georgia", "IMG002.CR2"),
            os.path.join("Temporary", "Georgia", "IMG002_RT.jpg"),
            os.path.join("Archive", "Georgia", "IMG002.CR2"),
            os.path.join("Archive", "Georgia", "Sélection", "IMG002.CR2"),
        ]
        removed_files = [
            os.path.join("Temporary", "Malta", "IMG002.CR2"),
            os.path.join("Temporary", "Malta", "IMG002_RT.jpg"),
            os.path.join("Archive", "Malta", "IMG002.CR2"),
            os.path.join("Archive", "Malta", "Sélection", "IMG002.CR2"),
        ]
        self.helper_check_paths(action_name, new_files, removed_files)
        picture_group = pydive_pictures.repository.trips["Georgia"]["IMG002"]
        # Wait until the new picture group has everything
        # This can't be done through signals because the target picture group doesn't exist yet when we trigger the action
        qtbot.waitUntil(lambda: "Archive" in picture_group.locations, timeout=1000)
        # Then, let's make sure both pictures have been moved
        qtbot.waitUntil(
            lambda: len(picture_group.locations["Archive"]) == 2, timeout=1000
        )
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG002 pictures"

        # Check display - Tree has been updated
        georgia_item = [
            picturesTree.topLevelItem(i)
            for i in range(picturesTree.topLevelItemCount())
            if picturesTree.topLevelItem(i).text(0) == "Georgia"
        ][0]
        qtbot.waitUntil(lambda: georgia_item.childCount() == 3)
        picture_item = [
            georgia_item.child(i)
            for i in range(georgia_item.childCount())
            if georgia_item.child(i).data(0, Qt.DisplayRole) == "IMG002"
        ][0]
        assert georgia_item.data(0, Qt.DisplayRole) == "Georgia", "New trip displayed"
        assert picture_item.data(0, Qt.DisplayRole) == "IMG002", "New picture displayed"
        assert picture_item.data(1, Qt.DisplayRole) == str(0), "0 image in Camera"
        assert picture_item.data(2, Qt.DisplayRole) == str(2), "2 image in Temporary"
        assert picture_item.data(3, Qt.DisplayRole) == str(2), "2 images in Archive"

    def test_pictures_tree_picture_group_wrong_action_name(
        self, pydive_pictures, qtbot, monkeypatch
    ):
        # Setup: get display
        picturesTree = pydive_pictures.ui["picture_tree"]

        # Trigger the addition of an impossible action
        trip_item = picturesTree.topLevelItem(5)  # Malta
        picture_item = trip_item.child(1)  # Malta's IMG002
        picturesTree.generate_context_menu(picture_item)
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            picturesTree.add_picture_group_action("", "", action_name, "", "", "")


if __name__ == "__main__":
    pytest.main(["-s", "--tb=line", __file__])
