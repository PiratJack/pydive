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
    def pydive_pictures(self, pydive_mainwindow, pydive_real_pictures):
        pydive_mainwindow.display_tab("Pictures")
        pydive_mainwindow.controllers["Pictures"].on_load_pictures()
        self.all_files = pydive_real_pictures

        yield pydive_mainwindow.layout.currentWidget()

    @pytest.fixture
    def pydive_ui(self, pydive_pictures, pydive_repository):
        def get_ui(element):
            left_column_items = [
                "folders",
                "load_pictures",
                "tree",
                "display_raw",
                "display_absent",
                "sort_mode",
                "tasks_label",
                "tasks_bar",
            ]
            # Overall elements
            if element == "layout":
                return pydive_pictures.layout()

            elif element == "left_column":
                return pydive_pictures.layout().itemAt(0).widget().layout()
            elif element in left_column_items:
                position = left_column_items.index(element)
                return get_ui("left_column").itemAt(position).widget()

            # Tree & tree items
            elif element == "tree":
                return get_ui("left_column").itemAt(2).widget()
            elif element.startswith("tree_"):
                split = element.split("_")[1:]
                if "convert" in split:
                    index = split.index("convert")
                    split = (
                        split[: index - 1]
                        + ["_".join(split[index - 1 : index + 1])]
                        + split[index + 1 :]
                    )
                # Looking for a trip
                if len(split) == 1:
                    return [
                        get_ui("tree").topLevelItem(i)
                        for i in range(get_ui("tree").topLevelItemCount())
                        if get_ui("tree").topLevelItem(i).text(0) == split[0]
                    ][0]
                # Looking for a picture group
                elif len(split) == 2:
                    parent = get_ui("tree_" + split[0])
                    item = [
                        parent.child(i)
                        for i in range(parent.childCount())
                        if parent.child(i).data(0, Qt.DisplayRole) == "IMG" + split[1]
                    ][0]
                    return item
                # Looking for a column
                elif len(split) == 3:
                    item = get_ui("_".join(["tree", split[0], split[1]]))
                    return item.data(int(split[2][3:]), Qt.DisplayRole)
                # Looking for a column, but number is like "010_convert"
                elif len(split) >= 3:
                    number = "_".join(split[1:-1])
                    column = int(split[-1][3:])
                    item = get_ui("_".join(["tree", split[0], number]))
                    return item.data(int(column), Qt.DisplayRole)

            # Not UI elements, but still very useful
            elif element.startswith("pg_"):
                split = element.split("_")
                if len(split) >= 3:
                    country = split[1]
                    number = "_".join(split[2:])
                else:
                    country, number = split[1:]
                return pydive_repository.trips[country]["IMG" + number]

            # Right column - with grid
            elif element == "right_column":
                return pydive_pictures.layout().itemAt(1).widget().layout()
            elif element == "grid":
                return get_ui("right_column").layout().itemAt(0).widget().layout()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    @pytest.fixture
    def pydive_picture_ui(self, pydive_ui):
        def get_element(row, col, element):
            # In order:
            #  If no image: spacer, generate, copy, spacer
            #  If image: spacer, delete, spacer, 1 button per category, spacer
            button_positions = {
                "generate": 1,
                "delete": 1,
                "copy": 2,
                "categoryTop": 3,
                "categoryBof": 4,
                "category3": 5,
            }

            container = pydive_ui("grid").itemAtPosition(row, col).widget()
            if element == "container":
                return container
            elif element in button_positions:
                buttonbox = container.layout().itemAt(1).widget()
                return buttonbox.layout().itemAt(button_positions[element]).widget()
            elif element == "filename":
                return container.layout().itemAt(0).widget()
            elif element == "error_if_no_image":
                return container.layout().itemAt(2).widget()
            elif element == "picture":
                return container.layout().itemAt(2).widget()
            elif element == "error_if_image":
                return container.layout().itemAt(3).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_element

    def click_tree_item(self, item, qtbot, pydive_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = pydive_ui("tree").visualItemRect(item).topLeft()
        qtbot.mouseClick(
            pydive_ui("tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def trigger_action(self, pydive_ui, item, menu_name, submenu_name=None):
        action_name = submenu_name if submenu_name else menu_name

        pydive_ui("tree").generate_context_menu(item)
        if submenu_name:
            menu = [
                m
                for m in pydive_ui("tree").menu.children()
                if isinstance(m, QtWidgets.QMenu) and m.title() == menu_name
            ][0]
        else:
            menu = pydive_ui("tree").menu
        action = [a for a in menu.actions() if a.text() == action_name][0]
        # Trigger action
        action.trigger()

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
        buttonbox = container.layout().itemAt(1).widget()

        if display_type in ("JPG", "RAW"):
            assert container.layout().count() == 3, test + " : Container display"
            assert buttonbox.layout().count() == 6, test + " : Buttonbox display"
            filename = container.layout().itemAt(0).widget()
            delete = buttonbox.layout().itemAt(1).widget()
            categoryTop = buttonbox.layout().itemAt(3).widget()
            categoryBof = buttonbox.layout().itemAt(4).widget()
            assert filename.text() == path, test + " : filename display"
            assert isinstance(delete, IconButton), test + " : delete display"
            assert isinstance(categoryTop, IconButton), test + " : categoryTop display"
            assert categoryTop.toolTip() == "Top", test + " : categoryTop display"
            assert isinstance(categoryBof, IconButton), test + " : categoryBof display"
            assert categoryBof.toolTip() == "Bof", test + " : categoryBof display"
            if display_type == "JPG":
                picture = container.layout().itemAt(2).widget()
                assert isinstance(picture, PictureDisplay), test + " : image display"
        elif display_type == "No image":
            assert container.layout().count() in (2, 3), test + " : Container display"
            # 2 or 3 depending on whether we have a spacer at the end
            assert buttonbox.layout().count() == 4, test + " : Buttonbox display"
            label = container.layout().itemAt(0).widget()
            generate = buttonbox.layout().itemAt(1).widget()  # 0 & 3 are spacers
            copy = buttonbox.layout().itemAt(2).widget()  # 0 & 3 are spacers
            assert label.text() == "No image", test + " : label display"
            assert isinstance(generate, IconButton), test + " : generate display"
            assert isinstance(copy, IconButton), test + " : copy display"
        else:
            raise ValueError("display_type should be RAW, JPG or No image")

    ########## Check display on the screen & action of checkboxes ########
    def test_pictures_display_overall(self, pydive_ui):
        # Check display - Overall structure
        assert isinstance(
            pydive_ui("layout"), QtWidgets.QHBoxLayout
        ), "Pictures layout is correct"
        assert (
            pydive_ui("layout").count() == 2
        ), "Pictures layout has the right number of columns"

        # Check display - Left column
        assert isinstance(
            pydive_ui("left_column"), QtWidgets.QVBoxLayout
        ), "Pictures left column layout is correct"
        assert (
            pydive_ui("left_column").count() == 8
        ), "Pictures left column has the right number of rows"

        # Check display - Left column - Checkboxes
        assert isinstance(
            pydive_ui("display_raw"), QtWidgets.QCheckBox
        ), "Pictures: Display RAW images is a QCheckBox"
        assert (
            pydive_ui("display_raw").text() == "Display RAW images"
        ), "Pictures: Display RAW images label text is correct"

        assert isinstance(
            pydive_ui("display_absent"), QtWidgets.QCheckBox
        ), "Pictures: Display absent images is QCheckBox"
        assert (
            pydive_ui("display_absent").text() == "Display absent images"
        ), "Pictures: Display absent images label is correct"

        assert isinstance(
            pydive_ui("sort_mode"), QtWidgets.QCheckBox
        ), "Pictures: Sort mode is QCheckBox"
        assert (
            pydive_ui("sort_mode").text()
            == "Sort mode: switch to next image when clicking on a category"
        ), "Pictures: Sort mode label is correct"

        # Check display - Left column - Tasks label & progress bar
        assert isinstance(
            pydive_ui("tasks_label"), QtWidgets.QLabel
        ), "Pictures: In-progress task label is QLabel"
        assert (
            pydive_ui("tasks_label").text() == "In-progress tasks: 0"
        ), "Pictures: In-progress task label text is correct"

        assert isinstance(
            pydive_ui("tasks_bar"), QtWidgets.QProgressBar
        ), "Pictures: In-progress task progress bar is QProgressBar"
        assert (
            pydive_ui("tasks_bar").text() == ""
        ), "Pictures: In-progress task progress bar value is correct"

        # Check display - Right column
        assert isinstance(
            pydive_ui("right_column"), QtWidgets.QVBoxLayout
        ), "Pictures right column layout is correct"
        assert (
            pydive_ui("right_column").count() == 1
        ), "Pictures right column has the right number of rows"

    def test_pictures_display_folders(self, pydive_ui, pydive_mainwindow, pydive_db):
        # Setup: get display
        folders = pydive_db.storagelocations_get_picture_folders()
        # Check what happens when display is refreshed twice in a row
        pydive_mainwindow.controllers["Pictures"].refresh_display()

        # Check display - Overall structure
        assert (
            pydive_ui("folders").layout().columnCount() == 2
        ), "Folders display has the right number of colums"
        assert pydive_ui("folders").layout().rowCount() == len(
            folders
        ), "Folders display has the right number of rows"

        # Check display - Folder names
        name_label = pydive_ui("folders").layout().itemAtPosition(0, 0).widget()
        assert isinstance(name_label, QtWidgets.QLabel), "Name field is a QLabel"
        assert (
            name_label.text() == folders[0].name
        ), "Name field displays the expected data"

        # Check display - Path display
        path_label = pydive_ui("folders").layout().itemAtPosition(0, 1).widget()
        assert isinstance(path_label, QtWidgets.QLineEdit), "Path field is a QLineEdit"
        assert (
            path_label.text() == folders[0].path
        ), "Path field displays the expected data"

    def test_pictures_display_tree_load_pictures(self, pydive_ui, qtbot):
        # Load pictures
        qtbot.mouseClick(pydive_ui("load_pictures"), Qt.LeftButton)
        # Second time to test refresh of already-displayed data
        qtbot.mouseClick(pydive_ui("load_pictures"), Qt.LeftButton)

        # Check display - Tree has the right number of columns
        assert (
            pydive_ui("tree").columnCount() == 6
        ), "Picture tree has the right number of columns"

        # Check display - Tree has the right number of high-level items
        assert (
            pydive_ui("tree").topLevelItemCount() == 7
        ), "Found the right number of trips"

        # Check display - Malta's images
        malta = pydive_ui("tree_Malta")
        malta_children = [malta.child(i).text(0) for i in range(malta.childCount())]
        assert malta.childCount() == 2, "Malta's children count is OK"
        assert malta_children == ["IMG001", "IMG002"], "Malta's children are OK"

    def test_pictures_display_checkboxes(self, pydive_ui, qtbot):
        # Get tree item, trip & picture group
        pydive_ui("tree_Malta").setExpanded(True)
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        offset = QtCore.QPoint(2, 5)  # This is just a guess to end up on the checkbox

        def check_hidden(grid, hidden_rows, hidden_columns, hidden_cells={}):
            for row in range(grid.layout().rowCount()):
                for col in range(grid.layout().columnCount()):
                    container = grid.layout().itemAtPosition(row, col).widget()
                    if row in hidden_rows or col in hidden_columns:
                        assert container.isHidden(), "Element is properly hidden"
                    elif row in hidden_cells and col in hidden_cells[row]:
                        assert container.isHidden(), "Element is properly hidden"
                    else:
                        assert not container.isHidden(), "Element is properly visible"

        # Check display - Correct display of columns & rows
        hidden_columns = [1, 2]  # RAW (hidden by default), DT (no image)
        hidden_rows = [
            1,
            2,
            3,
            4,
        ]
        # Archive (only RAW image), Camera, Inexistant, No picture here (no in any of those)
        check_hidden(pydive_ui("grid"), hidden_rows, hidden_columns)

        # Display RAW images ==> 1st column should be displayed
        qtbot.mouseClick(pydive_ui("display_raw"), Qt.LeftButton, Qt.NoModifier, offset)
        assert pydive_ui("display_raw").isChecked(), "Checkbox is indeed checked"
        hidden_columns = [2]  # DT (no image)
        hidden_rows = [
            2,
            3,
            4,
        ]
        # Camera, Inexistant, No picture here (no in any of those)
        hidden_cells = {1: [3]}
        # Row 1: col 1 is RAW and present, 2 is hidden already, 3 is RT doesn't exist
        # Rows 2-4 are hidden already
        # Row 5: col 1 is RAW and present, 2 is hidden already, 3 is RT and exists ==> all displayed
        check_hidden(pydive_ui("grid"), hidden_rows, hidden_columns, hidden_cells)

        # Display empty images ==> Everything should be displayed
        qtbot.mouseClick(
            pydive_ui("display_absent"), Qt.LeftButton, Qt.NoModifier, offset
        )
        assert pydive_ui("display_absent").isChecked(), "Checkbox is indeed checked"
        hidden_columns = []
        hidden_rows = []
        hidden_cells = {}
        check_hidden(pydive_ui("grid"), hidden_rows, hidden_columns, hidden_cells)

        # Display empty but not RAW images ==> 1st column should be hidden
        qtbot.mouseClick(pydive_ui("display_raw"), Qt.LeftButton, Qt.NoModifier, offset)
        assert not pydive_ui("display_raw").isChecked(), "Checkbox is indeed unchecked"
        hidden_columns = [1]  # RAW
        hidden_rows = []  # All displayed due to "display absent" being checked
        check_hidden(pydive_ui("grid"), hidden_rows, hidden_columns)

    def test_pictures_display_in_progress_tasks(self, pydive_ui, qtbot):
        # Trigger the conversion
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        self.trigger_action(
            pydive_ui, pydive_ui("tree_Malta_002"), menu_name, action_name
        )

        # Check results while task is running
        assert (
            pydive_ui("tasks_label").text() == "In-progress tasks: 1"
        ), "Pictures: In-progress task label text is correct"
        assert (
            pydive_ui("tasks_bar").text() == "0%"
        ), "Pictures: In-progress task progress bar value is correct"

        # Check results after task is complete
        qtbot.waitUntil(
            lambda: pydive_ui("tasks_label").text() == "In-progress tasks: 0"
        )
        assert (
            pydive_ui("tasks_bar").text() == "100%"
        ), "Pictures: In-progress task progress bar value is correct"

        # Check files are created
        new_files = [
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_display_grid(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger display of picture grid (twice to check if it handles it well)
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        # Check display - Overall grid structure
        assert (
            pydive_ui("grid").columnCount() == 4
        ), "PictureGrid has right number of columns"
        assert pydive_ui("grid").rowCount() == 6, "PictureGrid has right number of rows"

        # Check display - Correct display of different images (RAW, JPG, no image)
        # "No image"
        test = "No image"
        container = pydive_ui("grid").itemAtPosition(1, 2).widget()
        self.helper_check_picture_display(test, container, "No image")

        # RAW image ==> readable
        test = "RAW image"
        container = pydive_ui("grid").itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "RAW", "IMG001.CR2")
        assert not pydive_picture_ui(
            1, 1, "categoryTop"
        ).isChecked(), "Image not in Top"
        assert pydive_picture_ui(1, 1, "categoryBof").isChecked(), "Image in Bof"

        # JPG image ==> readable
        test = "JPG image"
        container = pydive_ui("grid").itemAtPosition(5, 3).widget()
        self.helper_check_picture_display(test, container, "JPG", "IMG001_RT.jpg")
        assert not pydive_picture_ui(
            5, 3, "categoryTop"
        ).isChecked(), "Image not in Top"
        assert not pydive_picture_ui(
            5, 3, "categoryBof"
        ).isChecked(), "Image not in Bof"

    ########## Check process group modal screen ########
    def test_pictures_process_groups_display(self, pydive_ui, qtbot, qapp):
        def handle_dialog():
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"
            # The actual contents of the dialog are handled in the other tests
            dialog.close()

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(pydive_ui("tasks_label"), Qt.LeftButton)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(700, handle_dialog)
        qtbot.mouseClick(pydive_ui("tasks_bar"), Qt.LeftButton)

    def test_pictures_process_groups_multiple_errors(self, pydive_ui, qtbot, qapp):
        # Trigger a copy (to get proper display)
        action_name = "Copy all images from Temporary to Archive"
        self.trigger_action(pydive_ui, pydive_ui("tree_Malta"), action_name)

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
        qtbot.mouseClick(pydive_ui("tasks_label"), Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
            os.path.join("Archive", "Malta", "IMG002_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_process_groups_one_error(self, pydive_ui, qtbot, qapp):
        # Trigger a copy (to get proper display)
        action_name = "Copy all images from Temporary to Archive"
        self.trigger_action(pydive_ui, pydive_ui("tree_Malta_001"), action_name)

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
        qtbot.mouseClick(pydive_ui("tasks_label"), Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    def test_pictures_process_groups_no_error(self, pydive_ui, qtbot, qapp):
        # Trigger a copy (to get proper display)
        action_name = "Copy all images from Temporary to Camera"
        self.trigger_action(pydive_ui, pydive_ui("tree_Malta_001"), action_name)

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
        qtbot.mouseClick(pydive_ui("tasks_label"), Qt.LeftButton)

        # Check files have been created & models updated
        new_files = [
            os.path.join("DCIM", "Malta", "IMG001.CR2"),
            os.path.join("DCIM", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)

    ########## Check actions on tree items ########
    def test_pictures_tree_click_trip(self, pydive_ui, qtbot):
        # Click on trip - should not display the picture grid
        self.click_tree_item(pydive_ui("tree_Georgia"), qtbot, pydive_ui)

        # Check display - Grid should not be displayed
        assert pydive_ui("grid").columnCount() == 1, "PictureGrid is empty"
        assert pydive_ui("grid").rowCount() == 1, "PictureGrid is empty"
        assert pydive_ui("grid").itemAtPosition(0, 0) is None, "PictureGrid is empty"

    def test_pictures_tree_click_picture_group_some_are_hidden(self, pydive_ui, qtbot):
        # Get tree item, trip & picture groups
        pydive_ui("tree_Malta").setExpanded(True)
        topleft = (
            pydive_ui("tree").visualItemRect(pydive_ui("tree_Malta_001")).topLeft()
        )

        # Trigger display of picture grid
        qtbot.mouseClick(
            pydive_ui("tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

        # Hide RAW and absent images
        qtbot.mouseClick(pydive_ui("display_raw"), Qt.LeftButton)
        qtbot.mouseClick(pydive_ui("display_absent"), Qt.LeftButton)

        # The display can't be checked because the window is not displayed
        # Therefore, widget.isVisible() will always be False

        # ## "No image"
        # #test = "No image"
        # #container = pydive_ui('grid').itemAtPosition(1, 2).widget()
        # #assert container.isVisible() == False, "Container is hidden"

        # ## RAW image ==> readable
        # #test = "RAW image"
        # #container = pydive_ui('grid').itemAtPosition(1, 1).widget()
        # #assert container.isVisible() == False, "Container is hidden"

        # ## JPG image ==> readable
        # #test = "JPG image"
        # #container = pydive_ui('grid').itemAtPosition(5, 3).widget()
        # #assert container.isVisible() == True, "Container is visible"

        pass

    def test_pictures_tree_remove_already_removed_picture_group(self, pydive_ui, qtbot):
        # Should not trigger errors
        picture_item = pydive_ui("tree_Malta_001")
        pydive_ui("tree").remove_picture_group(picture_item)
        pydive_ui("tree").remove_picture_group(picture_item)
        pydive_ui("tree").remove_picture_group(None)

    def test_pictures_tree_picture_group_removed_before_add_again(
        self, pydive_ui, pydive_picture_ui, qtbot
    ):
        # Trigger action
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        qtbot.mouseClick(pydive_picture_ui(1, 2, "generate"), Qt.LeftButton)

        # Empty tree to force a RuntimeError
        pydive_ui("tree").clear()

        # Check signal is emitted, file have been added & models updated
        new_path = os.path.join("Archive", "Malta", "IMG001_DT.jpg")
        new_files = [new_path]
        self.helper_check_paths("Generated image", new_files)

        qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureAdded)

    ########## Check actions on tree items - Trip-related menu actions ########
    def test_pictures_tree_trip_copy(self, pydive_ui, qtbot):
        # Trigger action
        trip_item = pydive_ui("tree_Georgia")
        picture_group_010 = pydive_ui("pg_Georgia_010")
        picture_group_011 = pydive_ui("pg_Georgia_011_convert")
        action_name = "Copy all images from Temporary to Archive"
        signals = [picture_group_010.pictureAdded] * 2 + [
            picture_group_011.pictureAdded
        ]
        with qtbot.waitSignals(signals, timeout=2000):
            self.trigger_action(pydive_ui, trip_item, action_name)

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
        assert pydive_ui("tree_Georgia_010_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_010_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Georgia_010_col3") == str(2), "2 in Archive"
        assert pydive_ui("tree_Georgia_011_convert_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_011_convert_col2") == str(1), "1 in Temporary"
        assert pydive_ui("tree_Georgia_011_convert_col3") == str(1), "1 in Archive"

    def test_pictures_tree_trip_convert(self, pydive_ui, qtbot):
        # Get tree item & picture groups
        trip_item = pydive_ui("tree_Malta")
        picture_group1 = pydive_ui("pg_Malta_001")
        picture_group2 = pydive_ui("pg_Malta_002")
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"

        # Trigger action
        signals = [picture_group1.pictureAdded, picture_group2.pictureAdded]
        with qtbot.waitSignals(signals, timeout=2000):
            self.trigger_action(pydive_ui, trip_item, menu_name, action_name)

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
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(3), "3 in Archive"
        assert pydive_ui("tree_Malta_002_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_002_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_002_col3") == str(3), "3 in Archive"

    def test_pictures_tree_trip_change_name(self, pydive_ui, qtbot, monkeypatch):
        # Trigger action
        trip_item = pydive_ui("tree_Korea")
        picture_group = pydive_ui("pg_Korea_030")
        action_name = "Change name to ..."
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            self.trigger_action(pydive_ui, trip_item, action_name)

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
        assert pydive_ui("tree_Italy") is not None, "Italy added to the tree"
        with pytest.raises(IndexError):
            pydive_ui("tree_Korea")
            pytest.fail("Korea removed from the tree")

    def test_pictures_tree_trip_change_name_exists(self, pydive_ui, qtbot, monkeypatch):
        # Trigger action
        trip_item = pydive_ui("tree_Korea")
        picture_group = pydive_ui("pg_Korea_030")
        action_name = "Change name to ..."
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )
        signals = [picture_group.pictureRemoved, picture_group.pictureRemoved]
        with qtbot.waitSignals(signals, timeout=2000):
            self.trigger_action(pydive_ui, trip_item, action_name)

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
        assert pydive_ui("tree_Georgia") is not None, "Georgia still in the tree"
        with pytest.raises(IndexError):
            pydive_ui("tree_Korea")
            pytest.fail("Korea removed from the tree")

    def test_pictures_tree_trip_wrong_action_name(self, pydive_ui, qtbot, monkeypatch):
        # Trigger the addition of an impossible action
        trip_item = pydive_ui("tree_Korea")
        pydive_ui("tree").generate_context_menu(trip_item)
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            pydive_ui("tree").add_trip_action("", "", action_name, "", "", "")

    ########## Check actions on tree items - Picture group-related menu actions ########
    def test_pictures_tree_picture_group_copy(self, pydive_ui, qtbot):
        # Trigger action
        picture_item = pydive_ui("tree_Malta_001")
        action_name = "Copy all images from Temporary to Archive"
        with qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureAdded, timeout=2000):
            self.trigger_action(pydive_ui, picture_item, action_name)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG001_RT.jpg"),
        ]
        self.helper_check_paths(action_name, new_files)
        assert (
            len(pydive_ui("pg_Malta_001").locations["Archive"]) == 3
        ), "Archive has 3 IMG001 pictures"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(3), "3 in Archive"

    def test_pictures_tree_picture_group_convert(self, pydive_ui, qtbot):
        # Trigger action
        picture_item = pydive_ui("tree_Malta_002")  # Malta's IMG002
        picture_group = pydive_ui("pg_Malta_002")
        menu_name = "Convert images in Archive"
        action_name = "Using DarkTherapee"
        with qtbot.waitSignal(picture_group.pictureAdded, timeout=2000):
            self.trigger_action(pydive_ui, picture_item, menu_name, action_name)

        # Check files have been created & models updated
        new_files = [
            os.path.join("Archive", "Malta", "IMG002_DT.jpg"),
        ]
        self.helper_check_paths(menu_name + " " + action_name, new_files)
        assert (
            len(picture_group.locations["Archive"]) == 3
        ), "Archive has 3 IMG002 pictures"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_002_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_002_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_002_col3") == str(3), "3 in Archive"

    def test_pictures_tree_picture_group_change_trip(
        self, pydive_ui, qtbot, monkeypatch
    ):
        # Trigger action
        action_name = "Change trip to ..."
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Italy", True)
        )
        with qtbot.waitSignal(pydive_ui("pg_Malta_002").pictureRemoved, timeout=2000):
            self.trigger_action(pydive_ui, pydive_ui("tree_Malta_002"), action_name)

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
        picture_group = pydive_ui("pg_Italy_002")
        # Wait until the new picture group has everything
        # This can't be done through signals because the target picture group doesn't exist yet when we trigger the action
        qtbot.waitUntil(lambda: "Archive" in picture_group.locations)
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG002 pictures"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Italy_002_col0") == "IMG002", "New picture displayed"
        assert pydive_ui("tree_Italy_002_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Italy_002_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Italy_002_col3") == str(2), "2 in Archive"

    def test_pictures_tree_picture_group_change_trip_target_exists(
        self, pydive_ui, qtbot, monkeypatch
    ):
        # Trigger action
        action_name = "Change trip to ..."
        monkeypatch.setattr(
            QtWidgets.QInputDialog, "getText", lambda *args: ("Georgia", True)
        )
        with qtbot.waitSignal(pydive_ui("pg_Malta_002").pictureRemoved, timeout=2000):
            self.trigger_action(pydive_ui, pydive_ui("tree_Malta_002"), action_name)

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
        picture_group = pydive_ui("pg_Georgia_002")
        # Wait until the new picture group has everything
        # This can't be done through signals because the target picture group doesn't exist yet when we trigger the action
        qtbot.waitUntil(lambda: "Archive" in picture_group.locations, timeout=1000)
        qtbot.waitUntil(
            lambda: len(picture_group.locations["Archive"]) == 2, timeout=1000
        )
        assert (
            len(picture_group.locations["Archive"]) == 2
        ), "Archive has 2 IMG002 pictures"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Georgia_002_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_002_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Georgia_002_col3") == str(2), "2 in Archive"

    def test_pictures_tree_picture_group_wrong_action_name(self, pydive_ui):
        # Trigger the addition of an impossible action
        pydive_ui("tree").generate_context_menu(pydive_ui("tree_Malta_002"))
        action_name = "Action does not exist"
        with pytest.raises(ValueError):
            pydive_ui("tree").add_picture_group_action("", "", action_name, "", "", "")

    ########## Check actions in the picture grid ########
    def test_pictures_grid_copy_raw_picture(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger display of grid
        picture_group = pydive_ui("pg_Georgia_010")
        self.click_tree_item(pydive_ui("tree_Georgia_010"), qtbot, pydive_ui)

        # Check display - No image displayed
        test = "Before RAW copy"
        container = pydive_ui("grid").itemAtPosition(1, 1).widget()
        self.helper_check_picture_display(test, container, "No image")

        # Trigger action
        with qtbot.waitSignal(picture_group.pictureAdded) as blocker:
            qtbot.mouseClick(pydive_picture_ui(1, 1, "copy"), Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join("Archive", "Georgia", "IMG010.CR2")
        new_files = [new_path]
        self.helper_check_paths("Copy RAW image", new_files)
        assert blocker.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "Added picture signal has correct path"
        assert blocker.args[1] == "", "Added picture signal has empty conversion method"
        assert len(picture_group.pictures[""]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After RAW copy"
        container = pydive_picture_ui(1, 1, "container")
        self.helper_check_picture_display(test, container, "RAW", "IMG010.CR2")

        # Check display - Tree has been updated
        assert pydive_ui("tree_Georgia_010_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_010_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Georgia_010_col3") == str(1), "1 in Archive"
        assert pydive_ui("tree_Georgia_011_convert_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_011_convert_col2") == str(1), "1 in Temporary"
        assert pydive_ui("tree_Georgia_011_convert_col3") == str(0), "0 in Archive"

    def test_pictures_grid_copy_jpg_picture(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger display of picture grid
        picture_group = pydive_ui("pg_Georgia_010")
        self.click_tree_item(pydive_ui("tree_Georgia_010"), qtbot, pydive_ui)

        # Check display - No image displayed
        test = "Before JPG copy"
        container = pydive_picture_ui(1, 3, "container")
        self.helper_check_picture_display(test, container, "No image")

        # Trigger action
        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(pydive_picture_ui(1, 3, "copy"), Qt.LeftButton)

        # Check signal is emitted, files have been created & models updated
        new_path = os.path.join("Archive", "Georgia", "IMG010_RT.jpg")
        new_files = [new_path]
        self.helper_check_paths("Copy JPG image", new_files)
        assert signal.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "Added picture signal has correct path"
        assert signal.args[1] == "RT", "Addition signal has RT as conversion"
        assert len(picture_group.pictures["RT"]) == 2, "New picture in group"

        # Check display - New image is displayed
        test = "After JPG copy"
        container = pydive_picture_ui(1, 3, "container")
        self.helper_check_picture_display(test, container, "JPG", "IMG010_RT.jpg")

        # Check display - Tree has been updated
        assert pydive_ui("tree_Georgia_010_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_010_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Georgia_010_col3") == str(1), "1 in Archive"
        assert pydive_ui("tree_Georgia_011_convert_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Georgia_011_convert_col2") == str(1), "1 in Temporary"
        assert pydive_ui("tree_Georgia_011_convert_col3") == str(0), "0 in Archive"

    def test_pictures_grid_copy_error(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger action - Should raise (caught) exception
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        qtbot.mouseClick(pydive_picture_ui(2, 2, "copy"), Qt.LeftButton)

        # Check display - Error is displayed
        error = pydive_picture_ui(2, 2, "error_if_no_image")
        assert error.text() == "No source image found", "Error is displayed"

    def test_pictures_grid_delete_jpg_picture(
        self, pydive_ui, pydive_picture_ui, qtbot, monkeypatch
    ):
        # Trigger display of picture grid
        picture_group = pydive_ui("pg_Malta_001")
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        # Trigger action
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        with qtbot.waitSignal(picture_group.pictureRemoved, timeout=1000) as signal:
            qtbot.mouseClick(pydive_picture_ui(5, 3, "delete"), Qt.LeftButton)

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
        container = pydive_picture_ui(5, 3, "container")
        self.helper_check_picture_display(test, container, "No image")

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(1), "1 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(2), "2 in Archive"

    def test_pictures_grid_delete_raw_picture(
        self, pydive_ui, pydive_picture_ui, qtbot, monkeypatch
    ):
        # Trigger display of picture grid
        picture_group = pydive_ui("pg_Malta_001")
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        # Trigger action
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "exec", lambda *args: QtWidgets.QMessageBox.Yes
        )
        with qtbot.waitSignals(
            [picture_group.pictureRemoved] * 2, timeout=1000
        ) as signals:
            qtbot.mouseClick(pydive_picture_ui(1, 1, "delete"), Qt.LeftButton)

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
        container = pydive_picture_ui(1, 1, "container")
        self.helper_check_picture_display(test, container, "No image")

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(0), "0 in Archive"

    def test_pictures_grid_convert_picture(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger action
        picture_group = pydive_ui("pg_Malta_001")
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(pydive_picture_ui(1, 2, "generate"), Qt.LeftButton)

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
        container = pydive_picture_ui(1, 2, "container")
        # This is called with "RAW" because the "conversion" is only a copy in this test
        self.helper_check_picture_display(test, container, "RAW", "IMG001_DT.jpg")

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(3), "3 in Archive"

    def test_pictures_grid_convert_picture_no_method_found(
        self, pydive_ui, pydive_picture_ui, qtbot
    ):
        # Trigger action - Should raise (caught) exception
        self.click_tree_item(pydive_ui("tree_Sweden_040"), qtbot, pydive_ui)
        qtbot.mouseClick(pydive_picture_ui(2, 4, "generate"), Qt.LeftButton)

        # Check display - Error is displayed
        error = pydive_picture_ui(2, 4, "error_if_no_image")
        assert error.text() == "No conversion method found", "Error is displayed"

    def test_pictures_grid_picture_zoom(
        self, pydive_ui, pydive_picture_ui, qtbot, qapp
    ):
        # Trigger display of picture grid
        self.click_tree_item(pydive_ui("tree_Sweden_040"), qtbot, pydive_ui)

        # Trigger mouse wheel
        picture = pydive_picture_ui(5, 2, "picture")
        size_before = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        with qtbot.waitSignal(picture.zoomChanged):
            self.mouseWheelTurn(qapp, picture, picture.pos(), 1)

        # Check results
        size_after = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        picture2 = pydive_picture_ui(5, 3, "picture")
        size_picture_2 = picture2.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        delta_zoom = abs(size_after - size_picture_2) / size_after
        assert size_before < size_after, "Picture is zoomed in"
        assert picture._zoom == 1, "Picture _zoom changed"
        assert delta_zoom < 0.01, "Other pictures are zoomed in with same zoom"
        assert picture2._zoom == 1, "Other pictures' _zoom property changed"

        # Zoom back to the original level
        with qtbot.waitSignal(picture.zoomChanged):
            self.mouseWheelTurn(qapp, picture, picture.pos(), -1)

        # Check results
        size_final = picture.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        size_picture_2 = picture2.transform().mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        delta_zoom = abs(size_final - size_picture_2) / size_after
        assert size_final < size_after, "Picture is back to original zoom level"
        assert size_final == size_before, "Picture is back to original zoom level"
        assert picture._zoom == 0, "Picture _zoom is back to original value"
        assert delta_zoom < 0.01, "Other pictures are zoomed in with same zoom"
        assert picture2._zoom == 0, "Other pictures' _zoom property changed"

    def test_pictures_grid_picture_move(
        self, pydive_ui, pydive_picture_ui, qtbot, qapp
    ):
        # Trigger display of picture grid
        self.click_tree_item(pydive_ui("tree_Sweden_040"), qtbot, pydive_ui)

        # Trigger mouse wheel
        picture = pydive_picture_ui(5, 2, "picture")
        picture2 = pydive_picture_ui(5, 3, "picture")
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

        # Trigger horizontal scrollbar
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
        assert scrollbarh2.value() == scrollbarh.value(), "Other pictures move too"

        # Trigger vertical scrollbar
        # I couldn't find how to trigger the mouse move event, so I trigger the signal directly
        scrollbarv = picture.verticalScrollBar()
        scrollbarv.valueChanged.emit(15)

        # Check results
        scrollbarv2 = picture2.verticalScrollBar()
        assert scrollbarv2.value() == scrollbarv.value(), "Other pictures move too"

    def test_pictures_grid_add_category(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger action
        picture_group = pydive_ui("pg_Malta_001")
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        with qtbot.waitSignal(picture_group.pictureAdded) as signal:
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)

        # Check signal is emitted, file have been added & models updated
        new_path = os.path.join("Temporary", "Malta", "Bof", "IMG001_RT.jpg")
        new_files = [new_path]
        self.helper_check_paths("Add to category", new_files)
        assert signal.args[0].path == os.path.join(
            pytest.BASE_FOLDER, new_path
        ), "New picture has correct path"
        assert signal.args[1] == "RT", "New picture has correct conversion method"
        assert len(picture_group.pictures["RT"]) == 2, "Picture has 2 RT images"

        # Check display - Category button is now checked
        assert pydive_picture_ui(5, 3, "categoryBof").isChecked(), "In Bof"
        assert not pydive_picture_ui(5, 3, "categoryTop").isChecked(), "Not in Top"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(3), "3 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(2), "2 in Archive"

    def test_pictures_grid_remove_category(self, pydive_ui, pydive_picture_ui, qtbot):
        # Trigger action
        picture_group = pydive_ui("pg_Malta_001")
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)

        with qtbot.waitSignal(picture_group.pictureRemoved) as signal:
            qtbot.mouseClick(pydive_picture_ui(1, 1, "categoryBof"), Qt.LeftButton)

        # Check signal is emitted, file have been added & models updated
        removed_files = [
            os.path.join("Archive", "Malta", "Bof", "IMG001.CR2"),
        ]
        self.helper_check_paths("Delete from category", [], removed_files)
        assert signal.args[0] == "", "Deletion signal has correct conversion type"
        assert signal.args[1].name == "Archive", "Deletion signal has correct location"
        assert len(picture_group.pictures[""]) == 2, "Picture has 2 RAW images"

        # Check display - Category button is now checked
        assert not pydive_picture_ui(1, 1, "categoryBof").isChecked(), "In Bof"
        assert not pydive_picture_ui(1, 1, "categoryTop").isChecked(), "Not in Top"

        # Check display - Tree has been updated
        assert pydive_ui("tree_Malta_001_col1") == str(0), "0 in Camera"
        assert pydive_ui("tree_Malta_001_col2") == str(2), "2 in Temporary"
        assert pydive_ui("tree_Malta_001_col3") == str(1), "1 in Archive"

    def test_pictures_grid_sort_mode_on(self, pydive_ui, pydive_picture_ui, qtbot):
        # Display pictures & enable sort mode
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        qtbot.mouseClick(pydive_ui("sort_mode"), Qt.LeftButton)
        assert pydive_ui("sort_mode").isChecked(), "Sort mode enabled"

        # Trigger action
        with qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureAdded):
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)

        # Check tree selection has changed
        selection = pydive_ui("tree").selectedItems()[0]
        assert selection == pydive_ui("tree_Malta_002"), "Selection has changed"

        # Should not move when removing a category
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        with qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureRemoved, timeout=300):
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)
        selection = pydive_ui("tree").selectedItems()[0]
        assert selection == pydive_ui("tree_Malta_001"), "Selection has not changed"

        # Can't go to next one when we're at the end
        self.click_tree_item(pydive_ui("tree_Malta_002"), qtbot, pydive_ui)
        with qtbot.waitSignal(pydive_ui("pg_Malta_002").pictureAdded):
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)
        selection = pydive_ui("tree").selectedItems()[0]
        assert selection == pydive_ui("tree_Malta_002"), "Selection has changed"

    def test_pictures_grid_sort_mode_off(self, pydive_ui, pydive_picture_ui, qtbot):
        # Display pictures
        self.click_tree_item(pydive_ui("tree_Malta_001"), qtbot, pydive_ui)
        assert not pydive_ui("sort_mode").isChecked(), "Sort mode disabled"

        # Trigger action (addition of category)
        with qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureAdded):
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)

        # Check tree selection has not changed
        selection = pydive_ui("tree").selectedItems()[0]
        assert selection == pydive_ui("tree_Malta_001"), "Selection has not changed"

        # Trigger action (deletion of category)
        with qtbot.waitSignal(pydive_ui("pg_Malta_001").pictureRemoved):
            qtbot.mouseClick(pydive_picture_ui(5, 3, "categoryBof"), Qt.LeftButton)

        # Check tree selection has not changed
        selection = pydive_ui("tree").selectedItems()[0]
        assert selection == pydive_ui("tree_Malta_001"), "Selection has not changed"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
