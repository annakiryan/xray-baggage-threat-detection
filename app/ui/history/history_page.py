from typing import Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from app.session.session_history_service import SessionHistoryService
from app.ui.history.widgets import (
    HistorySearchBar,
    SessionContentsGroup,
    SessionReviewViewerGroup,
    SessionsListGroup,
)
from app.ui.styles import SESSION_HISTORY_STYLE


class HistoryPage(QWidget):
    def __init__(self, results_dir: str):
        super().__init__()

        self.results_dir = results_dir
        self.all_sessions: list[dict[str, Any]] = []
        self.filtered_sessions: list[dict[str, Any]] = []
        self.current_session: Optional[dict[str, Any]] = None
        self.current_query = ""

        self._build_ui()
        self._apply_styles()
        self._connect_signals()
        self._load_sessions()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.page_root = QWidget()
        self.page_root.setObjectName("historyPageRoot")

        page_layout = QVBoxLayout(self.page_root)
        page_layout.setContentsMargins(16, 16, 16, 16)
        page_layout.setSpacing(12)

        self.search_bar = HistorySearchBar()

        content_row = QWidget()
        content_layout = QHBoxLayout(content_row)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.sessions_list_group = SessionsListGroup()
        self.sessions_list_group.setMinimumWidth(220)
        self.sessions_list_group.setMaximumWidth(280)

        self.session_contents_group = SessionContentsGroup()
        self.session_contents_group.setMinimumWidth(260)
        self.session_contents_group.setMaximumWidth(340)

        self.viewer_group = SessionReviewViewerGroup()

        content_layout.addWidget(self.sessions_list_group, 1)
        content_layout.addWidget(self.session_contents_group, 1)
        content_layout.addWidget(self.viewer_group, 3)

        page_layout.addWidget(self.search_bar)
        page_layout.addWidget(content_row, 1)

        root_layout.addWidget(self.page_root)

    def _apply_styles(self) -> None:
        self.page_root.setStyleSheet(SESSION_HISTORY_STYLE)

    def _connect_signals(self) -> None:
        self.search_bar.search_changed.connect(self._apply_filter)
        self.sessions_list_group.session_selected.connect(self._on_session_selected)
        self.session_contents_group.content_selected.connect(self._on_content_selected)

    def _load_sessions(self) -> None:
        sessions = SessionHistoryService.load_sessions(self.results_dir)

        for session in sessions:
            auto_images = SessionHistoryService.load_images_from_dir(
                session.get("detections_dir")
            )
            manual_images = SessionHistoryService.load_images_from_dir(
                session.get("manual_captures_dir")
            )

            session["auto_images"] = auto_images
            session["manual_images"] = manual_images
            session["auto_captures_count"] = len(auto_images)
            session["manual_captures_count"] = len(manual_images)

        self.all_sessions = sessions
        self._apply_filter(self.current_query)

    def reload_sessions(self) -> None:
        self.current_session = None
        self._load_sessions()

    def _apply_filter(self, query: str) -> None:
        self.current_query = query
        self.filtered_sessions = SessionHistoryService.filter_sessions(
            self.all_sessions,
            query,
        )
        self.sessions_list_group.set_sessions(self.filtered_sessions)

        if not self.filtered_sessions:
            self.current_session = None
            self.session_contents_group.set_session({})
            self.viewer_group.show_statistics({})

    def _on_session_selected(self, session: dict[str, Any]) -> None:
        self.current_session = session if session else None

        if not session:
            self.session_contents_group.set_session({})
            self.viewer_group.show_statistics({})
            return

        filtered_content = SessionHistoryService.filter_session_content(
            session,
            self.current_query,
        )
        self.session_contents_group.set_session(session, filtered_content=filtered_content)
        self.viewer_group.show_statistics(session)

    def _on_content_selected(self, content: dict[str, Any]) -> None:
        if not self.current_session:
            self.viewer_group.show_statistics({})
            return

        content_type = content.get("type")

        if content_type == SessionContentsGroup.ROOT_STATISTICS:
            self.viewer_group.show_statistics(self.current_session)
            return

        if content_type == SessionContentsGroup.ROOT_AUTO:
            self.viewer_group.show_placeholder_for_folder("Автоматические снимки")
            return

        if content_type == SessionContentsGroup.ROOT_MANUAL:
            self.viewer_group.show_placeholder_for_folder("Ручные снимки")
            return

        if content_type == SessionContentsGroup.ITEM_IMAGE:
            self.viewer_group.show_image(content.get("path"))
            return

        self.viewer_group.show_statistics(self.current_session)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        if hasattr(self, "viewer_group"):
            self.viewer_group.resize_viewer()