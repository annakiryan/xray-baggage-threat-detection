from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.session.analysis_session import AnalysisSession
from app.ui.main_window.navigation_rail import NavigationRail
from app.ui.styles import MAIN_WINDOW_STYLE


class MainWindow(QMainWindow):
    def __init__(
        self,
        analysis_page: QWidget,
        history_page: QWidget,
        session: AnalysisSession,
    ):
        super().__init__()

        self.analysis_session = session
        self.analysis_page = analysis_page
        self.history_page = history_page

        self.setWindowTitle("Детекция запрещённых предметов")

        self._build_ui()
        self._apply_styles()
        self._connect_signals()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.navigation_rail = NavigationRail()

        self.pages_stack = QStackedWidget()
        self.pages_stack.addWidget(self.analysis_page)
        self.pages_stack.addWidget(self.history_page)

        root_layout.addWidget(self.navigation_rail)
        root_layout.addWidget(self.pages_stack, 1)

    def _apply_styles(self) -> None:
        self.setStyleSheet(MAIN_WINDOW_STYLE)

    def _connect_signals(self) -> None:
        self.navigation_rail.analysis_requested.connect(self._show_analysis_page)
        self.navigation_rail.history_requested.connect(self._show_history_page)

    def _show_analysis_page(self) -> None:
        self.pages_stack.setCurrentWidget(self.analysis_page)

    def _show_history_page(self) -> None:
        if hasattr(self.history_page, "reload_sessions"):
            self.history_page.reload_sessions()

        self.pages_stack.setCurrentWidget(self.history_page)