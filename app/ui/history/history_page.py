from pathlib import Path
import qtawesome as qta

from PySide6.QtCore import Qt, QSize, QTimer, QEvent
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidgetItem,
    QPushButton,
    QWidget,
    QTableWidgetItem,
    QGraphicsBlurEffect,
    QLabel,
    QVBoxLayout,
)

from app.ui.history.widgets import SessionsPanel, HistoryViewerPanel, StatsPanel
from app.session.session_history_service import HistorySessionData, SessionHistoryService
from app.ui.styles import SESSION_HISTORY_STYLE

class HistoryPage(QWidget):
    def __init__(self, results_dir: str):
        super().__init__()

        self.results_dir = Path(results_dir)
        self.sessions: list[HistorySessionData] = []
        self.current_session: HistorySessionData | None = None
        self.current_images: list[Path] = []
        self.current_image_index = 0

        self.setObjectName("historyPageRoot")
        self.setStyleSheet(SESSION_HISTORY_STYLE)

        self._build_ui()
        self.reload_sessions()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sessions_panel = SessionsPanel()
        self.viewer_panel = HistoryViewerPanel()
        self.stats_panel = StatsPanel()

        self.search_input = self.sessions_panel.search_input
        self.sessions_list = self.sessions_panel.sessions_list

        self.session_title = self.viewer_panel.session_title
        self.tabs = self.viewer_panel.tabs
        self.image_label = self.viewer_panel.image_label
        self.counter_label = self.viewer_panel.counter_label
        self.prev_button = self.viewer_panel.prev_button
        self.next_button = self.viewer_panel.next_button
        self.thumbnails_layout = self.viewer_panel.thumbnails_layout
        self.thumbnails_scroll = self.viewer_panel.thumbnails_scroll
        self.thumbnail_buttons = []

        self.stats_table = self.stats_panel.stats_table
        self.total_label = self.stats_panel.total_label

        self.search_input.textChanged.connect(self._filter_sessions)
        self.sessions_list.itemSelectionChanged.connect(self._on_session_selected)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.prev_button.clicked.connect(self._show_prev_image)
        self.next_button.clicked.connect(self._show_next_image)

        self.image_label.clicked.connect(self._open_image_fullscreen)
        self.image_label.setCursor(self._make_zoom_cursor("fa5s.search-plus"))
        self._build_fullscreen_overlay()

        root.addWidget(self.sessions_panel)
        root.addWidget(self.viewer_panel, 1)
        root.addWidget(self.stats_panel)

    def reload_sessions(self):
        self.sessions = SessionHistoryService.load_sessions(self.results_dir)
        self._fill_sessions_list(self.sessions)

        if self.sessions:
            self.sessions_list.setCurrentRow(0)
        else:
            self._clear_viewer()

    def _fill_sessions_list(self, sessions: list[HistorySessionData]):
        self.sessions_list.clear()

        for session in sessions:
            item = QListWidgetItem(session.title)
            item.setData(Qt.UserRole, session)
            self.sessions_list.addItem(item)

    def _filter_sessions(self, text: str):
        query = text.strip().lower()

        if not query:
            self._fill_sessions_list(self.sessions)
            return

        filtered = [
            session for session in self.sessions if query in session.title.lower()
        ]

        self._fill_sessions_list(filtered)

    def _on_session_selected(self):
        items = self.sessions_list.selectedItems()
        if not items:
            return

        self.current_session = items[0].data(Qt.UserRole)
        self.session_title.setText(self.current_session.title)

        self._fill_stats(self.current_session)
        self._load_current_tab_images()

    def _on_tab_changed(self):
        self._load_current_tab_images()

    def _load_current_tab_images(self):
        if self.current_session is None:
            self._clear_viewer()
            return

        if self.tabs.currentIndex() == 0:
            self.current_images = self.current_session.detection_images
        else:
            self.current_images = self.current_session.manual_images

        self.current_image_index = 0
        self._render_current_image()
        self._render_thumbnails()

    def _render_current_image(self):
        total = len(self.current_images)

        if total == 0:
            self.image_label.setText("Нет снимков")
            self.image_label.setPixmap(QPixmap())
            self.counter_label.setText("Снимки: 0 из 0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return

        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < total - 1)
        self.counter_label.setText(f"Снимки: {self.current_image_index + 1} из {total}")

        pixmap = QPixmap(str(self.current_images[self.current_image_index]))
        self._set_preview_pixmap(pixmap)

    def _set_preview_pixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            self.image_label.setText("Не удалось открыть снимок")
            return

        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _render_thumbnails(self):
        while self.thumbnails_layout.count():
            item = self.thumbnails_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.thumbnail_buttons = []

        for index, image_path in enumerate(self.current_images):
            button = QPushButton()
            button.setObjectName("thumbnailButton")
            button.setCheckable(True)
            button.setChecked(index == self.current_image_index)
            button.setFixedSize(122, 86)
            button.setIconSize(QSize(112, 72))

            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                button.setIcon(
                    pixmap.scaled(
                        112,
                        72,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )

            button.clicked.connect(lambda _, i=index: self._select_image(i))

            self.thumbnail_buttons.append(button)
            self.thumbnails_layout.addWidget(button)

        self.thumbnails_layout.addStretch()

        QTimer.singleShot(0, self._scroll_to_current_thumbnail)

    def _select_image(self, index: int):
        self.current_image_index = index
        self._render_current_image()
        self._render_thumbnails()

    def _show_prev_image(self):
        if self.current_image_index > 0:
            self._select_image(self.current_image_index - 1)

    def _show_next_image(self):
        if self.current_image_index < len(self.current_images) - 1:
            self._select_image(self.current_image_index + 1)

    def _fill_stats(self, session: HistorySessionData):
        counts = session.class_counts
        self.stats_table.setRowCount(len(counts))

        total = 0

        for row, (class_name, count) in enumerate(counts.items()):
            total += int(count)

            class_item = QTableWidgetItem(class_name)
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.stats_table.setItem(row, 0, class_item)
            self.stats_table.setItem(row, 1, count_item)

        self.total_label.setText(f"Всего обнаружений: {total}")

    def _clear_viewer(self):
        self.current_session = None
        self.current_images = []

        self.session_title.setText("Сессия не выбрана")
        self.image_label.setText("Нет снимков")
        self.image_label.setPixmap(QPixmap())
        self.counter_label.setText("Снимки: 0 из 0")

        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)

        self.stats_table.setRowCount(0)
        self.total_label.setText("Всего обнаружений: 0")

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.current_images:
            self._render_current_image()

    def _scroll_to_current_thumbnail(self):
        if not self.thumbnail_buttons:
            return

        if self.current_image_index >= len(self.thumbnail_buttons):
            return

        current_button = self.thumbnail_buttons[self.current_image_index]
        self.thumbnails_scroll.ensureWidgetVisible(current_button, 24, 0)

    def _build_fullscreen_overlay(self):
        self.fullscreen_overlay = QWidget(self)
        self.fullscreen_overlay.setObjectName("imageFullscreenOverlay")
        self.fullscreen_overlay.hide()
        self.fullscreen_overlay.installEventFilter(self)

        overlay_layout = QVBoxLayout(self.fullscreen_overlay)
        overlay_layout.setContentsMargins(48, 48, 48, 48)

        self.fullscreen_image_label = QLabel()
        self.fullscreen_image_label.setObjectName("fullscreenImageLabel")
        self.fullscreen_image_label.setAlignment(Qt.AlignCenter)
        self.fullscreen_image_label.setCursor(
            self._make_zoom_cursor("fa5s.search-minus")
        )
        self.fullscreen_image_label.installEventFilter(self)

        overlay_layout.addWidget(self.fullscreen_image_label)

    def _open_image_fullscreen(self):
        if not self.current_images:
            return

        pixmap = QPixmap(str(self.current_images[self.current_image_index]))
        if pixmap.isNull():
            return

        self._set_background_blur(True)

        self.fullscreen_overlay.setGeometry(self.rect())
        self.fullscreen_overlay.show()
        self.fullscreen_overlay.raise_()

        scaled = pixmap.scaled(
            self.fullscreen_overlay.size() * 0.9,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.fullscreen_image_label.setPixmap(scaled)

    def _close_image_fullscreen(self):
        self.fullscreen_overlay.hide()
        self.fullscreen_image_label.clear()
        self._set_background_blur(False)

    def _set_background_blur(self, enabled: bool):
        panels = [
            self.sessions_panel,
            self.viewer_panel,
            self.stats_panel,
        ]

        for panel in panels:
            if enabled:
                blur = QGraphicsBlurEffect()
                blur.setBlurRadius(8)
                panel.setGraphicsEffect(blur)
            else:
                panel.setGraphicsEffect(None)

    def _make_zoom_cursor(self, icon_name: str) -> QCursor:
        icon = qta.icon(icon_name, color="#E6EAF0")
        pixmap = icon.pixmap(24, 24)
        return QCursor(pixmap, 8, 8)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress:
            if watched in (self.fullscreen_overlay, self.fullscreen_image_label):
                self._close_image_fullscreen()
                return True

        return super().eventFilter(watched, event)
