import gettext

from PyQt5 import QtWidgets, QtCore
from .iconbutton import IconButton

_ = gettext.gettext


class PathSelectButton(IconButton):
    pathSelected = QtCore.pyqtSignal(str)

    def __init__(self, image, parent=None, target_type="folder"):
        super().__init__(image, "", parent)
        self.target_type = "folder" if target_type == "folder" else "file"
        self.setIcon(image)
        self.clicked.connect(self.choose_path)

        self.dialog = QtWidgets.QFileDialog(self)

        self.target = None

    def choose_path(self):
        if self.target_type == "folder":
            self.target = self.dialog.getExistingDirectory(self, _("Choose Directory"))
        else:
            self.target, _a = self.dialog.getOpenFileName(None, _("Choose File"))
        if self.target:
            self.pathSelected.emit(self.target)
            return self.target
