import os
import sys
import unittest
import logging
from PyQt5 import QtWidgets

sys.path.append("pydive")

import pydive
import pydive.controllers.mainwindow
import pydive.models.database as databasemodel

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"


class TestUiSettings(unittest.TestCase):
    def setUp(self):
        self.database = databasemodel.Database(DATABASE_FILE)
        if sys.platform == "linux":
            os.environ["QT_QPA_PLATFORM"] = "xcb"
        self.app = QtWidgets.QApplication(sys.argv)
        self.mainwindow = pydive.controllers.mainwindow.MainWindow(self.database)

    def tearDown(self):
        self.mainwindow.close()
        self.mainwindow.database.session.close()
        self.mainwindow.database.engine.dispose()
        self.app.quit()
        self.app.deleteLater()
        # ## Delete database
        os.remove(DATABASE_FILE)

    def test_mainwindow_toolbar(self):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesController.toolbar_button.trigger()
        self.assertEqual(
            self.mainwindow.layout.currentIndex(), 1, "Pictures screen now displayed"
        )
