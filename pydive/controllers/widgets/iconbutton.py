import gettext

from PyQt5 import QtWidgets, QtCore, QtGui

_ = gettext.gettext


class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon=None, label=None, parent=None):
        if icon:
            super(IconButton, self).__init__(icon, label, parent)
        else:
            super(IconButton, self).__init__(label, parent)

        self.pad = 6  # padding between the icon and the button frame
        self.minSize = 24  # minimum size of the icon

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.setMinimumSize(self.pad * 2 + self.minSize, self.pad * 2 + self.minSize)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHorizontalStretch(0)
        self.setSizePolicy(sizePolicy)
        self.setSizeIncrement(0, 0)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)

        # ---- get default style ----

        opt = QtWidgets.QStyleOptionButton()
        self.initStyleOption(opt)

        # ---- scale icon to button size ----

        Rect = opt.rect

        h = Rect.height()
        w = Rect.width()
        iconSize = max(min(h, w) - 2 * self.pad, self.minSize)

        opt.iconSize = QtCore.QSize(iconSize, iconSize)

        # ---- draw button ----

        self.style().drawControl(QtWidgets.QStyle.CE_PushButton, opt, qp, self)

        qp.end()
