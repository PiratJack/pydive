import gettext

from PyQt5 import QtWidgets, QtCore

_ = gettext.gettext


class PathSelectButton(QtWidgets.QPushButton):
    pathSelected = QtCore.pyqtSignal(str)

    def __init__(self, label, target_type="folder"):
        super().__init__()
        self.target_type = "folder" if target_type == "folder" else "file"
        self.setText(_(label))
        self.clicked.connect(self.choose_path)

        self.dialog = QtWidgets.QFileDialog(self)

        self.target = None

    def choose_path(self):
        if self.target_type == "folder":
            self.target = self.dialog.getExistingDirectory(self, "Choose Directory")
        else:
            self.target, _ = self.dialog.getOpenFileName(None, "Choose File")
        self.pathSelected.emit(self.target)
        return self.target

    def set_path(self, path):
        self.target = path
