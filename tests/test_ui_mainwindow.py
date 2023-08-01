import os
import sys
import pytest
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))


import controllers.mainwindow
import models.database as databasemodel

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"


class TestUiSettings:
    @pytest.fixture(scope="function", autouse=True)
    def setup_and_teardown(self, qtbot):
        self.database = databasemodel.Database(DATABASE_FILE)
        self.mainwindow = controllers.mainwindow.MainWindow(self.database)

        yield

        self.mainwindow.database.session.close()
        self.mainwindow.database.engine.dispose()
        # Delete database
        os.remove(DATABASE_FILE)

    def test_mainwindow_toolbar(self):
        picturesController = self.mainwindow.controllers["Pictures"]
        picturesController.toolbar_button.trigger()
        assert (
            self.mainwindow.layout.currentIndex() == 1
        ), "Pictures screen now displayed"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
