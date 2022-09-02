"""Main application module"""
import gettext
import sys
import os
import PyQt5

import controllers.mainwindow

# Define some constants
LOCALE_FOLDER = "./locale"
STYLESHEET_FILE = "./assets/style/app.css"

# Setup translation
gettext.bindtextdomain("messages", LOCALE_FOLDER)
gettext.translation("messages", localedir=LOCALE_FOLDER).install()

if __name__ == "__main__":
    # Change platform to avoid Wayland-related warning messages
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    with open(STYLESHEET_FILE, "r") as stylesheet:
        app.setStyleSheet(stylesheet.read())

    window = controllers.mainwindow.MainWindow()
    window.showMaximized()
    app.exec_()
