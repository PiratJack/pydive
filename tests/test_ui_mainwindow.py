import os
import sys
import pytest
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "pydive"))

import models.database
import models.repository

import controllers.mainwindow

logging.basicConfig(level=logging.WARNING)

DATABASE_FILE = "test.sqlite"


class TestUiMainWindow:
    def test_mainwindow_toolbar(self, pydive_mainwindow):
        picturesController = pydive_mainwindow.controllers["Pictures"]
        picturesController.toolbar_button.trigger()
        assert (
            pydive_mainwindow.layout.currentIndex() == 1
        ), "Pictures screen now displayed"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
