"""ProcessGroups screen: Displays in-progress background process groups

Classes
----------
ProcessGroupsTableModel
    QAbstractModel for mapping of data
ProgressBarItemDelegate
    Delegate to display a progress bar rather than simple number
ProcessGroupsTableView
    QTableView for display of process groups
ProcessGroupsController
    ProcessGroups screen: Displays in-progress background process groups / tasks
"""
import gettext
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets import autoresize

_ = gettext.gettext
logger = logging.getLogger(__name__)

# TODO: Allow to cancel background processes
class ProcessGroupsTableModel(QtCore.QAbstractTableModel):
    """Model for display of transactions, based on user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column needs a name key (alignment & size are optional)
    database : models.database.Database
        A reference to the application database
    accounts : list of models.account.Account
        The accounts for filtering
    process_groups : list of models.repository.ProcessGroup
        The list of process groups to display

    Methods
    -------
    __init__ (database, columns)
        Stores the provided parameters for future use

    columnCount (index)
        Returns the number of columns
    rowCount (index)
        Returns the number of rows
    data (index)
        Returns which data to display (or how to display it) for the corresponding cell
    headerData (index)
        Returns the table headers

    set_filters (index)
        Applies the filters on the list of transactions
    get_transaction (index)
        Returns a models.transaction.Transaction object for the corresponding index
    """

    def __init__(self, repository, columns):
        """Stores the provided parameters for future use

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        columns : list of dicts
            Columns to display.
            Each column needs a name key (alignment & size are optional)
        """
        super().__init__()
        self.columns = columns
        self.repository = repository
        self.process_groups = []

    def columnCount(self, index):
        """Returns the number of columns

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.columns)

    def rowCount(self, index):
        """Returns the number of rows

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.process_groups)

    def data(self, index, role):
        """Returns the data or formatting to display in table contents

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole: the data to display
            If role = Qt.TextAlignmentRole: the proper alignment
        """
        if not index.isValid():
            return False

        col = index.column()
        process_group = self.process_groups[index.row()]
        errors = [
            t["error_details"] for t in process_group.tasks if "error_details" in t
        ]
        if role == Qt.DisplayRole:
            # TODO: Think about how to display the errors
            # Right now they're not very useful (lack details)
            if len(errors) == 0:
                error_text = ""
            if len(errors) <= 1:
                error_text = "".join(errors)
            else:
                error_text = _("Hover for error details")
            return [
                process_group.label,
                process_group.progress,
                process_group.count_completed,
                process_group.count_total,
                process_group.count_errors,
                error_text,
            ][col]

        if role == Qt.ToolTipRole and col == 5:
            return "\n".join(errors)

        if role == Qt.TextAlignmentRole:
            return self.columns[index.column()]["alignment"]

        return QtCore.QVariant()

    def headerData(self, column, orientation, role):
        """Returns the data or formatting to display in headers

        Parameters
        ----------
        column : int
            The column number
        orientation : Qt.Orientation
            Whether headers are horizontal or vertical
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole and orientation == Qt.Horizontal: the header name
            Else: QtCore.QVariant
        """
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return QtCore.QVariant(_(self.columns[column]["name"]))
        return QtCore.QVariant()

    def refresh_display(self):
        """Refreshes the list of process groups displayed"""
        self.process_groups = self.repository.process_groups
        for row, t in enumerate(self.process_groups):
            index1 = self.createIndex(row, 0, QtCore.QModelIndex())
            index2 = self.createIndex(row, len(self.columns), QtCore.QModelIndex())
            t.progressUpdate.connect(
                lambda index1=index1, index2=index2: self.dataChanged.emit(
                    index1, index2
                )
            )


class ProgressBarItemDelegate(QtWidgets.QAbstractItemDelegate):
    def paint(self, painter, option, index):
        progress_bar = QtWidgets.QStyleOptionProgressBar()
        progress_bar.rect = option.rect
        progress_bar.minimum = 0
        progress_bar.maximum = 100
        progress_bar.progress = int(index.data() * 100)
        progress_bar.text = "{}%".format(progress_bar.progress)
        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.CE_ProgressBar, progress_bar, painter
        )


class ProcessGroupsTableView(QtWidgets.QTableView, autoresize.AutoResize):
    """Table for display of process groups

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : TransactionsController
        The controller in which this class is displayed
    repository : models.repository.Repository
        A reference to the application repository
    model : ProcessGroupsTableModel
        The model for interaction with the repository

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters & connects with the model & user interactions
    """

    columns = [
        {
            "name": _("Tasks"),
            "size": 0.3,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Progress"),
            "size": 0.1,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Completed"),
            "size": 0.1,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Total"),
            "size": 0.1,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Errors"),
            "size": 0.1,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Details"),
            "size": 0.3,
            "alignment": Qt.AlignLeft,
        },
    ]
    transaction_details = None

    def __init__(self, parent_controller):
        """Stores parameters & connects with the model & user interactions

        Parameters
        ----------
        parent_controller : ProcessGroupsController
            The controller in which this table is displayed
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.repository = parent_controller.repository

        self.model = ProcessGroupsTableModel(self.repository, self.columns)
        self.setModel(self.model)
        self.progress_bar = ProgressBarItemDelegate(self)
        self.setItemDelegateForColumn(1, self.progress_bar)

    def refresh_display(self):
        """Refreshes the list of process groups displayed"""
        self.model.refresh_display()
        self.model.layoutChanged.emit()
        self.viewport().update()


class ProcessGroupsController:
    """ProcessGroups screen: Displays in-progress background process groups

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
    refresh_display
        Updates the list of in-progress process groups
    """

    name = _("In-progress tasks")
    code = "ProcessGroups"

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        logger.debug("SettingsController.init")
        self.parent_window = parent_window
        self.database = parent_window.database
        self.repository = parent_window.repository
        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QVBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        self.ui["process_groups_list_label"] = QtWidgets.QLabel(_("In-progress tasks"))
        self.ui["process_groups_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["process_groups_list_label"])

        self.process_groups_list = ProcessGroupsTableView(self)
        self.ui["process_groups_list"] = self.process_groups_list
        self.ui["layout"].addWidget(self.ui["process_groups_list"])

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        self.refresh_display()
        return self.ui["main"]

    def refresh_display(self):
        """Updates the process groups displayed on screen"""
        logger.debug("ProcessGroupsController.refresh_display")
        self.process_groups_list.refresh_display()
