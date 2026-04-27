from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.domain.settings import InterfaceSettings, get_bbox_color_hex
from app.session.analysis_session import AnalysisSession
from app.ui.history.history_page import HistoryPage
from app.ui.main_window.navigation_rail import NavigationRail
from app.ui.settings.settings_page import SettingsPage
from app.ui.styles import build_main_window_style, build_session_history_style


class MainWindow(QMainWindow):
    def __init__(
        self,
        analysis_page: QWidget,
        history_page: HistoryPage,
        settings_page: SettingsPage,
        session: AnalysisSession,
        interface_settings: InterfaceSettings,
        theme_manager,
    ):
        super().__init__()

        self.analysis_session = session
        self.analysis_page = analysis_page
        self.history_page = history_page
        self.settings_page = settings_page
        self.interface_settings = interface_settings
        self.theme_manager = theme_manager

        self.setWindowTitle("Детекция запрещённых предметов")

        self._build_ui()
        self._connect_signals()
        self._apply_interface_style()
        self._apply_detection_drawing_settings()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("mainCentralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.navigation_rail = NavigationRail()

        self.pages_stack = QStackedWidget()
        self.pages_stack.addWidget(self.analysis_page)
        self.pages_stack.addWidget(self.history_page)
        self.pages_stack.addWidget(self.settings_page)

        root_layout.addWidget(self.navigation_rail)
        root_layout.addWidget(self.pages_stack, 1)

    def _connect_signals(self) -> None:
        self.navigation_rail.analysis_requested.connect(self._show_analysis_page)
        self.navigation_rail.history_requested.connect(self._show_history_page)
        self.navigation_rail.settings_requested.connect(self._show_settings_page)

        self.settings_page.theme_changed.connect(self._apply_theme)
        self.settings_page.ui_scale_changed.connect(self._apply_ui_scale)
        self.settings_page.bbox_color_changed.connect(self._apply_bbox_color)
        self.settings_page.bbox_thickness_changed.connect(self._apply_bbox_thickness)

    def _show_analysis_page(self) -> None:
        self.pages_stack.setCurrentWidget(self.analysis_page)

    def _show_history_page(self) -> None:
        self.history_page.reload_sessions()
        self.pages_stack.setCurrentWidget(self.history_page)

    def _show_settings_page(self) -> None:
        self.pages_stack.setCurrentWidget(self.settings_page)

    def _apply_interface_style(self) -> None:
        palette = self.theme_manager.get_palette(self.interface_settings.theme_key)

        self.setStyleSheet(
            build_main_window_style(
                palette=palette,
                ui_scale=self.interface_settings.ui_scale,
            )
        )

        self.history_page.setStyleSheet(
            build_session_history_style(
                palette=palette,
                ui_scale=self.interface_settings.ui_scale,
            )
        )

    def _apply_theme(self, theme_key: str) -> None:
        self.interface_settings.theme_key = theme_key
        self._apply_interface_style()

    def _apply_ui_scale(self, ui_scale: int) -> None:
        self.interface_settings.ui_scale = ui_scale
        self._apply_interface_style()

    def _apply_detection_drawing_settings(self) -> None:
        self.analysis_session.set_bbox_color_hex(
            get_bbox_color_hex(self.interface_settings.bbox_color_key)
        )
        self.analysis_session.set_bbox_thickness(self.interface_settings.bbox_thickness)

    def _apply_bbox_color(self, color_key: str) -> None:
        self.interface_settings.bbox_color_key = color_key
        self.analysis_session.set_bbox_color_hex(get_bbox_color_hex(color_key))

    def _apply_bbox_thickness(self, thickness: int) -> None:
        self.interface_settings.bbox_thickness = thickness
        self.analysis_session.set_bbox_thickness(thickness)
