import gettext

from PyQt5 import QtWidgets, QtCore, QtGui

_ = gettext.gettext


class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon=None, label=None, parent=None):
        super(IconButton, self).__init__(icon, label, parent)

        self.pad = 8  # padding between the icon and the button frame
        self.minSize = 8  # minimum size of the icon

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHorizontalStretch(0)
        self.setSizePolicy(sizePolicy)
        self.setSizeIncrement(0, 0)

        size = QtCore.QSize(39, 36)
        # #self.setMinimumSize(size)
        # #self.setMaximumSize(size)

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
