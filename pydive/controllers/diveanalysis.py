"""Displays details of a dive and allows for more analysis

Classes
----------
DiveTree
    The tree displaying the dives
DiveAnalysisGraph
    The graph displaying the dive history
DiveAnalysisController
    Analysis & comments of a given dive
"""
import os
import gettext
import logging
import pyqtgraph

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from controllers.widgets.basetreewidget import BaseTreeWidget
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
        Stores reference to parent controller & repository
    fill_tree
        Adds all trips & dives to the tree
    dive_to_widget (dive)
        Converts a Dive object to a QTreeWidgetItem
    on_item_clicked (item)
        Item clicked ==> display corresponding dive
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
        self.setMinimumSize(550, 100)
        self.itemClicked.connect(self.on_item_clicked)

    def fill_tree(self):
        """Adds all trips & dives to the tree"""
        logger.info("DiveTree.fill_tree")
        self.clear()
        for element in reversed(self.divelog.dives):
            if element.type == "dive":
                widget = self.dive_to_widget(element)
                widget.model = element
                self.addTopLevelItem(widget)
            elif element.type == "trip":
                data = [element.name]
                widget = QtWidgets.QTreeWidgetItem(map(str, data))
                widget.model = element
                widget.setData(0, Qt.UserRole, element)
                self.addTopLevelItem(widget)
                for dive in reversed(element.dives):
                    dive_widget = self.dive_to_widget(dive)
                    dive_widget.model = dive
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
        widget.setData(0, Qt.UserRole, dive)
        return widget

    def on_item_clicked(self, item):
        """Item clicked ==> display corresponding dive

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
            The item that was clicked
        """
        logger.info(f"DiveTree.on_item_clicked: {item.data(0, Qt.DisplayRole)}")
        # Exclude clicks on trips
        if item.childCount() > 0 or not item.model:
            return

        self.parent_controller.display_dive(item.model)


class DiveAnalysisGraph:
    """The graph displaying the dive history

    Attributes
    ----------
    parent_controller : PicturesController
        A reference to the parent controller
    divelog: models.divelog.DiveLog
        The divelog to display
    dive: models.divelog.Dive
        The dive to display
    plots: dict of pyqtgraph.Plot
        The plots being displayed
    ui: dict of QtWidgets.QWidget items
        The different parts of the screen

    Methods
    -------
    __init__ (parent_controller)
        Stores reference to parent controller & divelog
    display_dive (dive)
        Reads a Dive and displays it in the graph
    clear_plots
        Clears all plot
    """

    def __init__(self, parent_controller):
        """Stores reference to parent controller

        Parameters
        ----------
        parent_controller : PicturesController
            A reference to the parent controller
        """
        logger.debug("DiveAnalysisGraph.init")
        self.parent_controller = parent_controller
        self.divelog = parent_controller.divelog
        self.dive = None
        self.plots = {}

        self.ui = {}
        self.ui["main"] = pyqtgraph.PlotWidget()
        self.ui["main"].showGrid(x=True, y=True)
        # #self.ui['main'].setAxisItems({"bottom": pyqtgraph.DateAxisItem()})
        self.ui["main"].getViewBox().invertY(True)
        background = (230, 230, 230)
        self.ui["main"].setBackground(background)
        self.ui["main"].getAxis("left").setTextPen("k")
        self.ui["main"].getAxis("bottom").setTextPen("k")
        self.ui["main"].addLegend()

    def display_dive(self, dive):
        """Reads a Dive and displays it in the graph

        Parameters
        ----------
        dive : models.divelog.Dive
            A dive from the divelog
        """
        logger.debug(f"DiveAnalysisGraph.display_dive {dive}")

        self.dive = dive

        self.clear_plots()

        # Calculate vertical speed (in m/minute)
        x_values = list(dive.depths.keys())
        # speeds has format x:speed after x
        speeds = {
            x: (dive.depths[x_values[idx + 1]] - dive.depths[x])
            / (x_values[idx + 1] - x)
            * 60
            for idx, x in enumerate(x_values[:-1])
        }

        # Group speed in categories
        # This is based on recommendations from FFESSM & usual computer speeds
        # Below 10m/min: OK (grey)
        # 10 to 15m/min: risky (orange)
        # Above 15m/min: very risky (red)
        def speed_to_color(speed):
            if speed <= -15:
                return "r"
            elif speed < -10:
                return (255, 165, 0)
            return (119, 136, 153)

        color_to_name = {
            "r": _("&gt;= 15 m/min (dangerous)"),
            (255, 165, 0): _("10-15 m/min (risky)"),
            (119, 136, 153): _("&lt;= 10 m/min (OK)"),
        }

        colors = {x: speed_to_color(speeds[x]) for x in speeds}

        # Plot the graphs
        plots = {}
        for color, plot_name in color_to_name.items():
            # Lines are drawn if they the 2 dots are included and have finite value in the values
            # We need to color each line depending on the speed
            # The "speeds" variable indicates the speed after the dot
            # Therefore, if speeds[x] is red, both x and the value right after x need to be included
            # Hence the check on x_values[idx-1]

            # This will generate shared segments
            # Because we plot in order grey, then orange, then red, the last color will take precedence
            # In other words, we plot the worst (most risky) color possible
            plots[color] = [
                dive.depths[x]
                if colors[x] == color
                or (x_values[idx - 1] in colors and colors[x_values[idx - 1]] == color)
                else float("inf")
                for idx, x in enumerate(x_values[:-1])
            ]
            # The computer keeps recording on the surface, so the last dot is most likely with null speed
            if color == "b":
                plots[color].append(dive.depths[x_values[-1]])
            else:
                plots[color].append(float("inf"))

            line = pyqtgraph.mkPen(color, width=3)

            self.plots[color] = self.ui["main"].plot(
                x=x_values,
                y=plots[color],
                pen=line,
                connect="finite",
                name=plot_name,
            )

        return self.ui["main"]

    @property
    def display_widget(self):
        """Returns the QtWidgets.QWidget for display of this screen"""

        return self.ui["main"]

    def clear_plots(self):
        """Clears all plots"""
        for plot_id, plot in self.plots.items():
            self.ui["main"].removeItem(plot)
            self.ui["main"].clear()
        self.plots = {}


class DiveAnalysisController:
    """Analysis & comments of a given dive

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
    graph : DiveAnalysisGraph
        The graph displaying the dive details
    dive_tree : DiveTree
        The tree of trips & dives displayed

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
    on_export
        Exports the graph with the comments added
    display_dive (dive)
        Displays a given dive on the graph
    refresh_display
        Refreshes the display - reloads the list of dives
    """

    name = _("Dive analysis")
    code = "DiveAnalysis"
    scan_file_split_mask = "%Y-%m-%d %Hh%M - Carnet.jpg"

    def __init__(self, parent_window):
        """Stores reference to parent window & defines UI elements.

        Parameters
        ----------
        parent_window : QtWidgets.QWidget (most likely QtWidgets.QMainWindow)
            The window displaying this controller
        """
        logger.debug("DiveAnalysisController.init")
        self.parent_window = parent_window
        self.database = parent_window.database
        self.divelog_path = None
        self.divelog = DiveLog()
        self.dive_tree = DiveTree(self)
        self.graph = DiveAnalysisGraph(self)

        self.ui = {}
        self.ui["main"] = QtWidgets.QWidget()
        self.ui["layout"] = QtWidgets.QHBoxLayout()
        self.ui["main"].setLayout(self.ui["layout"])

        ###### Left part: Error (if no file selected) + Display of pictures & dives ####
        self.ui["left"] = QtWidgets.QWidget()
        self.ui["left_layout"] = QtWidgets.QVBoxLayout()
        self.ui["left"].setLayout(self.ui["left_layout"])
        self.ui["layout"].addWidget(self.ui["left"], 1)

        self.ui["error"] = QtWidgets.QLabel()
        self.ui["error"].setProperty("class", "validation_error")
        self.ui["left_layout"].addWidget(self.ui["error"])

        self.ui["dive_tree"] = self.dive_tree
        self.ui["left_layout"].addWidget(self.ui["dive_tree"], 1)

        ###### Right part: Graph display & Export button ####
        self.ui["right"] = QtWidgets.QWidget()
        self.ui["right_layout"] = QtWidgets.QVBoxLayout()
        self.ui["right"].setLayout(self.ui["right_layout"])
        self.ui["layout"].addWidget(self.ui["right"], 5)

        # Graph
        self.ui["graph"] = self.graph.display_widget
        self.ui["right_layout"].addWidget(self.ui["graph"])

        # Validate button
        self.ui["export"] = QtWidgets.QPushButton(_("Export"))
        self.ui["export"].clicked.connect(self.on_export)
        self.ui["right_layout"].addWidget(self.ui["export"])

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
                + "/assets/images/graphs.png"
            ),
            self.name,
            self.parent_window,
        )
        button.setStatusTip(_("Dive analysis"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.code))
        return button

    def on_export(self):
        """Exports the graph with the comments added"""
        pass

    def display_dive(self, dive):
        """Displays the graph of a given dive

        Parameters
        ----------
        dive: models.divelog.Dive
            The dive to display
        """
        self.graph.display_dive(dive)

    def refresh_display(self):
        """Refreshes the display - reloads the list of dives"""
        logger.debug("DiveAnalysisController.refresh_display")

        # Reload divelog data
        divelog = self.database.storagelocations_get_divelog()
        self.divelog_path = divelog[0].path if divelog[0].path != " " else None
        try:
            self.divelog.load_dives(self.divelog_path)
            self.dive_tree.fill_tree()
            self.ui["error"].setText(None)
        except (IOError, ValueError) as e:
            self.ui["error"].setText(e.args[0])
