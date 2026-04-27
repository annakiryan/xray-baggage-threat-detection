from PySide6.QtCore import Qt, QSize, Signal
import qtawesome as qta
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QTabBar,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class SessionsPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("historySessionsPanel")
        self.setFixedWidth(300)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск сессии")

        self.sessions_list = QListWidget()

        title = QLabel("Сессии")
        title.setObjectName("panelTitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.sessions_list, 1)


class HistoryViewerPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("historyViewerPanel")

        self.session_title = QLabel("Сессия не выбрана")
        self.session_title.setObjectName("historySessionTitle")

        self.tabs = QTabBar()
        self.tabs.setDrawBase(False)
        self.tabs.setFocusPolicy(Qt.NoFocus)
        self.tabs.addTab("Автоматические снимки")
        self.tabs.addTab("Ручные снимки")

        self.image_label = ClickableImageLabel("Нет снимков")
        self.image_label.setObjectName("historyImageViewer")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(430)

        self.counter_label = QLabel("Снимки: 0 из 0")
        self.counter_label.setObjectName("mutedLabel")

        self.prev_button = QPushButton()
        self.next_button = QPushButton()

        self.prev_button.setIcon(qta.icon("fa5s.chevron-left", color="#E6EAF0"))
        self.next_button.setIcon(qta.icon("fa5s.chevron-right", color="#E6EAF0"))

        self.prev_button.setIconSize(QSize(14, 14))
        self.next_button.setIconSize(QSize(14, 14))

        self.prev_button.setObjectName("navArrowButton")
        self.next_button.setObjectName("navArrowButton")

        self.prev_button.setFixedSize(35, 30)
        self.next_button.setFixedSize(35, 30)

        self.thumbnails_scroll = QScrollArea()
        self.thumbnails_scroll.setWidgetResizable(True)
        self.thumbnails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumbnails_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumbnails_scroll.setMinimumHeight(124)

        self.thumbnails_widget = QWidget()
        self.thumbnails_layout = QHBoxLayout(self.thumbnails_widget)
        self.thumbnails_layout.setContentsMargins(0, 0, 0, 0)
        self.thumbnails_layout.setSpacing(10)
        self.thumbnails_scroll.setWidget(self.thumbnails_widget)

        self._build_layout()

    def _build_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.addWidget(self.session_title)
        header.addStretch()

        bottom = QFrame()
        bottom.setObjectName("historyBottomPanel")

        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 14, 16, 16)
        bottom_layout.setSpacing(12)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.counter_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)

        bottom_layout.addLayout(nav_layout)
        bottom_layout.addWidget(self.thumbnails_scroll)

        layout.addLayout(header)
        layout.addWidget(self.tabs)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(bottom)


class StatsPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("historyStatsPanel")
        self.setFixedWidth(300)

        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Категория", "Количество"])
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.stats_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.stats_table.setObjectName("statsTable")
        self.stats_table.setShowGrid(False)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setFrameShape(QFrame.NoFrame)
        self.stats_table.setFocusPolicy(Qt.NoFocus)
        self.stats_table.horizontalHeader().setHighlightSections(False)
        self.stats_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )
        self.stats_table.verticalHeader().setDefaultSectionSize(38)

        self.total_label = QLabel("Всего обнаружений: 0")
        self.total_label.setObjectName("statsTotalLabel")

        title = QLabel("Статистика")
        title.setObjectName("panelTitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(title)
        layout.addWidget(self.stats_table)
        layout.addWidget(self.total_label)
        layout.addStretch()


class ClickableImageLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
