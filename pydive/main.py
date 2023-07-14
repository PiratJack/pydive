"""Main application module"""
import gettext
import logging
import sys
import os
import platformdirs
import PyQt5

import models
import controllers.mainwindow
import models.database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PyDive:
    LOCALE_FOLDER = os.path.join(os.path.dirname(__file__), "locale")
    STYLESHEET_FILE = "./assets/style/app.css"
    DATABASE_FILE = "sandbox.sqlite"

    def __init__(self, database_file=None):
        if database_file:
            self.DATABASE_FILE = database_file
        elif "--real" in sys.argv:
            os.makedirs(
                platformdirs.user_data_dir("piratjack-pydive", "PiratJack"),
                exist_ok=True,
            )
            self.DATABASE_FILE = (
                platformdirs.user_data_dir("piratjack-pydive", "PiratJack")
                + "/prod.sqlite"
            )
            logger.setLevel(logging.ERROR)

        # Setup translation
        gettext.bindtextdomain("messages", self.LOCALE_FOLDER)
        gettext.translation(
            "messages", localedir=self.LOCALE_FOLDER, languages=["fr"]
        ).install()

        # Connect to database
        self.database = models.database.Database(self.DATABASE_FILE)

        # Change platform to avoid Wayland-related warning messages
        if sys.platform == "linux":
            os.environ["QT_QPA_PLATFORM"] = "xcb"

    def run(self):
        app = PyQt5.QtWidgets.QApplication(sys.argv)
        with open(self.STYLESHEET_FILE, "r", encoding="UTF-8") as stylesheet:
            app.setStyleSheet(stylesheet.read())

        window = controllers.mainwindow.MainWindow(self.database)
        window.showMaximized()
        app.exec_()


if __name__ == "__main__":
    app = PyDive()
    app.run()
