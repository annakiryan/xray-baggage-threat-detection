from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)


class HistorySearchBar(QWidget):
    search_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по сессиям, классам и файлам...")
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(340)
        self.search_input.setMaximumWidth(520)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self.search_input)
        layout.addStretch()


class SessionsListGroup(QGroupBox):
    session_selected = Signal(dict)

    def __init__(self):
        super().__init__("Сессии")

        self.sessions: list[dict[str, Any]] = []

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("historySessionsList")
        self.list_widget.currentRowChanged.connect(self._emit_selected_session)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def set_sessions(self, sessions: list[dict[str, Any]]) -> None:
        self.sessions = sessions
        self.list_widget.clear()

        for session in sessions:
            item = QListWidgetItem(self._format_session_title(session))
            self.list_widget.addItem(item)

        if sessions:
            self.list_widget.setCurrentRow(0)
        else:
            self.session_selected.emit({})

    def _emit_selected_session(self, row: int) -> None:
        if row < 0 or row >= len(self.sessions):
            self.session_selected.emit({})
            return

        self.session_selected.emit(self.sessions[row])

    @staticmethod
    def _format_session_title(session: dict[str, Any]) -> str:
        return str(session.get("started_at", "—"))


class SessionContentsGroup(QGroupBox):
    content_selected = Signal(dict)

    ROOT_STATISTICS = "statistics"
    ROOT_AUTO = "auto_images"
    ROOT_MANUAL = "manual_images"
    ITEM_IMAGE = "image"

    def __init__(self):
        super().__init__("Содержимое")

        self.current_session: Optional[dict[str, Any]] = None

        self.tree_widget = QTreeWidget()
        self.tree_widget.setObjectName("historyContentsTree")
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemSelectionChanged.connect(self._emit_selected_content)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.tree_widget)
        self.setLayout(layout)

    def set_session(
        self,
        session: dict[str, Any],
        filtered_content: Optional[dict[str, Any]] = None,
    ) -> None:
        self.current_session = session if session else None
        self.tree_widget.clear()

        if not session:
            self.content_selected.emit({})
            return

        content = filtered_content or {
            "show_statistics": True,
            "auto_images": session.get("auto_images", []),
            "manual_images": session.get("manual_images", []),
        }

        statistics_item = None
        if content.get("show_statistics", False):
            statistics_item = QTreeWidgetItem(["Статистика"])
            statistics_item.setData(0, Qt.UserRole, {"type": self.ROOT_STATISTICS})
            self.tree_widget.addTopLevelItem(statistics_item)

        auto_root = QTreeWidgetItem(["Автоматические снимки"])
        auto_root.setData(0, Qt.UserRole, {"type": self.ROOT_AUTO})
        self.tree_widget.addTopLevelItem(auto_root)

        for image_path in content.get("auto_images", []):
            child = QTreeWidgetItem([image_path.name])
            child.setData(
                0,
                Qt.UserRole,
                {
                    "type": self.ITEM_IMAGE,
                    "path": image_path,
                    "source": self.ROOT_AUTO,
                },
            )
            auto_root.addChild(child)

        manual_root = QTreeWidgetItem(["Ручные снимки"])
        manual_root.setData(0, Qt.UserRole, {"type": self.ROOT_MANUAL})
        self.tree_widget.addTopLevelItem(manual_root)

        for image_path in content.get("manual_images", []):
            child = QTreeWidgetItem([image_path.name])
            child.setData(
                0,
                Qt.UserRole,
                {
                    "type": self.ITEM_IMAGE,
                    "path": image_path,
                    "source": self.ROOT_MANUAL,
                },
            )
            manual_root.addChild(child)

        auto_root.setExpanded(True)
        manual_root.setExpanded(True)

        if statistics_item is not None:
            self.tree_widget.setCurrentItem(statistics_item)
        elif auto_root.childCount() > 0:
            self.tree_widget.setCurrentItem(auto_root.child(0))
        elif manual_root.childCount() > 0:
            self.tree_widget.setCurrentItem(manual_root.child(0))
        else:
            self.tree_widget.setCurrentItem(auto_root)

    def _emit_selected_content(self) -> None:
        item = self.tree_widget.currentItem()
        if item is None:
            self.content_selected.emit({})
            return

        data = item.data(0, Qt.UserRole)
        if not isinstance(data, dict):
            self.content_selected.emit({})
            return

        self.content_selected.emit(data)


class StatCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("statCard")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statCardTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statCardValue")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatisticsViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.title_label = QLabel("Статистика")
        self.title_label.setObjectName("historyViewerTitle")

        self.session_id_value = QLabel("—")
        self.video_path_value = QLabel("—")
        self.video_path_value.setWordWrap(True)
        self.started_at_value = QLabel("—")
        self.finished_at_value = QLabel("—")

        self.events_card = StatCard("Событий")
        self.auto_card = StatCard("Автоматических снимков")
        self.manual_card = StatCard("Ручных снимков")

        self.class_counts_text = QTextEdit()
        self.class_counts_text.setReadOnly(True)
        self.class_counts_text.setObjectName("summaryTextBlock")

        self._build_layout()
        self.set_empty_state()

    def _build_layout(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        root.addWidget(self.title_label)

        info_layout = QGridLayout()
        info_layout.setHorizontalSpacing(14)
        info_layout.setVerticalSpacing(10)
        info_layout.setColumnStretch(1, 1)

        info_layout.addWidget(self._make_caption("Session ID"), 0, 0)
        info_layout.addWidget(self.session_id_value, 0, 1)

        info_layout.addWidget(self._make_caption("Видео"), 1, 0)
        info_layout.addWidget(self.video_path_value, 1, 1)

        info_layout.addWidget(self._make_caption("Начало"), 2, 0)
        info_layout.addWidget(self.started_at_value, 2, 1)

        info_layout.addWidget(self._make_caption("Конец"), 3, 0)
        info_layout.addWidget(self.finished_at_value, 3, 1)

        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        root.addWidget(info_widget)

        cards_row = QWidget()
        cards_layout = QHBoxLayout(cards_row)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)
        cards_layout.addWidget(self.events_card)
        cards_layout.addWidget(self.auto_card)
        cards_layout.addWidget(self.manual_card)
        root.addWidget(cards_row)

        title = QLabel("Статистика по классам")
        title.setObjectName("summarySectionTitle")
        root.addWidget(title)

        self.class_counts_text.setMinimumHeight(220)
        root.addWidget(self.class_counts_text)

        root.addStretch()
        self.setLayout(root)

    def set_empty_state(self) -> None:
        self.session_id_value.setText("—")
        self.video_path_value.setText("—")
        self.started_at_value.setText("—")
        self.finished_at_value.setText("—")

        self.events_card.set_value("0")
        self.auto_card.set_value("0")
        self.manual_card.set_value("0")

        self.class_counts_text.setPlainText("Нет данных")

    def set_session(self, session: dict[str, Any]) -> None:
        if not session:
            self.set_empty_state()
            return

        self.session_id_value.setText(str(session.get("session_id", "—")))
        self.video_path_value.setText(str(session.get("video_path", "—")))
        self.started_at_value.setText(str(session.get("started_at", "—")))
        self.finished_at_value.setText(str(session.get("finished_at", "—")))

        self.events_card.set_value(str(session.get("total_detection_events", 0)))
        self.auto_card.set_value(str(session.get("auto_captures_count", 0)))
        self.manual_card.set_value(str(session.get("manual_captures_count", 0)))

        self.class_counts_text.setPlainText(
            self._format_class_counts(session.get("class_counts", {}))
        )

    @staticmethod
    def _make_caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("summaryCaption")
        return label

    @staticmethod
    def _format_class_counts(class_counts: dict[str, int]) -> str:
        if not class_counts:
            return "Нет обнаружений"

        lines = [
            f"• {class_name}: {count}"
            for class_name, count in sorted(
                class_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]
        return "\n".join(lines)


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.current_pixmap: Optional[QPixmap] = None

        self.title_label = QLabel("Просмотр изображения")
        self.title_label.setObjectName("historyViewerTitle")

        self.image_name_label = QLabel("—")
        self.image_name_label.setWordWrap(True)

        self.image_preview_label = QLabel("Нет изображения")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setObjectName("imageViewer")
        self.image_preview_label.setMinimumSize(400, 300)
        self.image_preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self._build_layout()

    def _build_layout(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)

        root.addWidget(self.title_label)
        root.addWidget(self.image_name_label)
        root.addWidget(self.image_preview_label, 1)

        self.setLayout(root)

    def clear(self, message: str = "Нет изображения") -> None:
        self.current_pixmap = None
        self.image_name_label.setText("—")
        self.image_preview_label.clear()
        self.image_preview_label.setText(message)

    def show_image(self, image_path: Path | None) -> None:
        if image_path is None:
            self.clear()
            return

        self.image_name_label.setText(image_path.name)

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.current_pixmap = None
            self.image_preview_label.setText("Не удалось загрузить изображение")
            return

        self.current_pixmap = pixmap
        self._update_scaled_preview()

    def resize_preview(self) -> None:
        if self.current_pixmap is not None:
            self._update_scaled_preview()

    def _update_scaled_preview(self) -> None:
        if self.current_pixmap is None:
            return

        target_size = self.image_preview_label.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self.current_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_preview_label.setPixmap(scaled)


class SessionReviewViewerGroup(QGroupBox):
    def __init__(self):
        super().__init__("Просмотр")

        self.statistics_view = StatisticsViewer()
        self.image_view = ImageViewer()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.statistics_view)
        self.stacked_widget.addWidget(self.image_view)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.show_statistics({})

    def show_statistics(self, session: dict[str, Any]) -> None:
        self.statistics_view.set_session(session)
        self.stacked_widget.setCurrentWidget(self.statistics_view)

    def show_image(self, image_path: Path | None) -> None:
        self.image_view.show_image(image_path)
        self.stacked_widget.setCurrentWidget(self.image_view)

    def show_placeholder_for_folder(self, title: str) -> None:
        self.image_view.clear(f'Выберите файл в разделе "{title}"')
        self.stacked_widget.setCurrentWidget(self.image_view)

    def resize_viewer(self) -> None:
        self.image_view.resize_preview()