from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta
from PySide6.QtCore import QSize


class NavigationRail(QWidget):
    analysis_requested = Signal()
    history_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("navigationRail")
        self.setFixedWidth(56)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.analysis_button = self._create_button(
            icon=qta.icon("fa5s.play-circle", color="#c5cdd8"),
            tooltip="Анализ",
        )
        self.history_button = self._create_button(
            icon=qta.icon("fa5s.history", color="#c5cdd8"),
            tooltip="История",
        )

        self.analysis_button.setChecked(True)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.analysis_button)
        self.button_group.addButton(self.history_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        layout.addWidget(self.analysis_button, alignment=Qt.AlignHCenter)
        layout.addWidget(self.history_button, alignment=Qt.AlignHCenter)
        layout.addStretch()

        self.analysis_button.clicked.connect(self.analysis_requested.emit)
        self.history_button.clicked.connect(self.history_requested.emit)

    def _create_button(self, icon, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setIcon(icon)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setAutoRaise(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        button.setIconSize(QSize(22, 22))
        button.setFixedSize(48, 48)
        return button