"""Tasks screen: Displays in-progress background tasks

Classes
----------
TasksController
    Tasks screen: Displays in-progress background tasks
"""
import gettext
import logging

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets import autoresize

_ = gettext.gettext
logger = logging.getLogger(__name__)


class TasksTableModel(QtCore.QAbstractTableModel):
    """Model for display of transactions, based on user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column needs a name key (alignment & size are optional)
    database : models.database.Database
        A reference to the application database
    accounts : list of models.account.Account
        The accounts for filtering
    tasks : list of models.repository.ProcessGroup
        The list of tasks (process groups) to display

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
        self.tasks = []

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
        return len(self.tasks)

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
        if role == Qt.DisplayRole:
            task = self.tasks[index.row()]
            return [
                task.label,
                task.progress,
                task.count_completed,
                task.count_total,
                task.count_errors,
                "",
            ][col]

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
        """Refreshes the list of tasks displayed"""
        self.tasks = self.repository.process_groups
        for row, t in enumerate(self.tasks):
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


class TasksTableView(QtWidgets.QTableView, autoresize.AutoResize):
    """Table for display of tasks

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : TransactionsController
        The controller in which this class is displayed
    repository : models.repository.Repository
        A reference to the application repository
    model : TasksTableModel
        The model for interaction with the repository

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters & connects with the model & user interactions
    """

    columns = [
        {
            "name": _("Task"),
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
        parent_controller : TasksController
            The controller in which this table is displayed
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.repository = parent_controller.repository

        self.model = TasksTableModel(self.repository, self.columns)
        self.setModel(self.model)
        self.progress_bar = ProgressBarItemDelegate(self)
        self.setItemDelegateForColumn(1, self.progress_bar)

    def refresh_display(self):
        """Refreshes the list of tasks displayed"""
        self.model.refresh_display()
        self.model.layoutChanged.emit()
        self.viewport().update()


class TasksController:
    """Tasks screen: Displays in-progress background tasks

    Attributes
    ----------
    name : str
        The name of this controller - displayed on top
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
        Updates the list of in-progress tasks
    """

    name = _("Tasks")

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

        self.ui["tasks_list_label"] = QtWidgets.QLabel(_("In-progress tasks"))
        self.ui["tasks_list_label"].setProperty("class", "title")
        self.ui["layout"].addWidget(self.ui["tasks_list_label"])

        self.tasks_list = TasksTableView(self)
        self.ui["tasks_list"] = self.tasks_list
        self.ui["layout"].addWidget(self.ui["tasks_list"])

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""
        self.refresh_display()
        return self.ui["main"]

    @property
    def toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/settings.png"), self.name, self.parent_window
        )
        button.setStatusTip(self.name)
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def refresh_display(self):
        """Updates the tasks displayed on screen"""
        logger.debug("TasksController.refresh_display")
        self.tasks_list.refresh_display()
