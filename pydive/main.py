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

# Define some constants
LOCALE_FOLDER = "./locale"
STYLESHEET_FILE = "./assets/style/app.css"
# Define some constants
DATABASE_FILE = "sandbox.sqlite"
if "--real" in sys.argv:
    os.makedirs(
        platformdirs.user_data_dir("piratjack-pydive", "PiratJack"),
        exist_ok=True,
    )
    DATABASE_FILE = (
        platformdirs.user_data_dir("piratjack-pydive", "PiratJack") + "/prod.sqlite"
    )
    logger.setLevel(logging.ERROR)

# Setup translation
gettext.bindtextdomain("messages", LOCALE_FOLDER)
gettext.translation("messages", localedir=LOCALE_FOLDER).install()

# Connect to database
database = models.database.Database(DATABASE_FILE)

if __name__ == "__main__":
    # Change platform to avoid Wayland-related warning messages
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    with open(STYLESHEET_FILE, "r", encoding="UTF-8") as stylesheet:
        app.setStyleSheet(stylesheet.read())

    window = controllers.mainwindow.MainWindow(database)
    window.showMaximized()
    app.exec_()
