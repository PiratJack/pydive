import gettext

from PyQt5 import QtWidgets, QtCore
from .iconbutton import IconButton

_ = gettext.gettext


class PathSelectButton(IconButton):
    pathSelected = QtCore.pyqtSignal(str)

    def __init__(self, image, parent=None, target_type="folder"):
        super().__init__(image, "", parent)
        self.target_type = target_type
        self.setIcon(image)
        self.clicked.connect(self.choose_path)

        self.dialog = QtWidgets.QFileDialog(self)

        self.target = None

    def choose_path(self):
        if self.target_type == "folder":
            self.target = self.dialog.getExistingDirectory(self, _("Choose Directory"))
        elif self.target_type == "file":
            self.target, _a = self.dialog.getOpenFileName(None, _("Choose File"))
        elif self.target_type == "new_file":
            self.target, _a = self.dialog.getSaveFileName(None, _("Choose File"))
        else:
            raise ValueError(f"Unknown type for PathSelectButton: {self.target_type}")
        if self.target:
            self.pathSelected.emit(self.target)
            return self.target
