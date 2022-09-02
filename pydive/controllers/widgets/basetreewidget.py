"""Helper class for trees - adds sorting, headers, ...

Classes
----------
BaseTreeWidget
    Helper class for trees - adds sorting, headers, ...
"""
import gettext

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from controllers.widgets import autoresize

_ = gettext.gettext


class BaseTreeWidget(QtWidgets.QTreeWidget, autoresize.AutoResize):
    """Helper class for trees - adds sorting, headers, ...

    Attributes
    ----------
    columns : list of dicts
        Columns to display. The name key is the only one used here (for headers)
    parent_controller : *Controller
        The controller in which this class is displayed

    Methods
    -------
    on_double_click (tree_item)
        Handler for clicks on tree items. By default, expands the item.
    """

    columns = {}

    def __init__(self, parent_controller):
        """Stores parameters & defines table characteristics (sort, column counts, ...)

        Parameters
        ----------
        parent_controller : controllers.*Controller
            The controller displaying this tree
        """
        super().__init__()
        self.parent_controller = parent_controller

        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])

        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
