from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta


class NavigationRail(QWidget):
    analysis_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("navigationRail")
        self.setFixedWidth(50)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.analysis_button = self._create_button("fa5s.desktop", "Анализ")
        self.history_button = self._create_button("fa5s.clock", "История")
        self.settings_button = self._create_button("fa5s.cog", "Настройки")

        self.analysis_button.setChecked(True)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.analysis_button)
        self.button_group.addButton(self.history_button)
        self.button_group.addButton(self.settings_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)

        layout.addWidget(self.analysis_button)
        layout.addWidget(self.history_button)
        layout.addWidget(self.settings_button)
        layout.addStretch()

        self.analysis_button.clicked.connect(self.analysis_requested.emit)
        self.history_button.clicked.connect(self.history_requested.emit)
        self.settings_button.clicked.connect(self.settings_requested.emit)

    def _create_button(self, icon_name: str, text: str) -> QToolButton:
        button = QToolButton()

        button.default_icon = qta.icon(icon_name, color="#8E99A8")
        button.active_icon = qta.icon(icon_name, color="#E6EAF0")

        button.setIcon(button.default_icon)
        button.setToolTip(text)
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        button.setIconSize(QSize(22, 22))
        button.setFixedSize(50, 50)

        button.toggled.connect(
            lambda checked, b=button: b.setIcon(
                b.active_icon if checked else b.default_icon
            )
        )

        return button
