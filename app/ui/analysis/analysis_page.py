from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from app.domain.entities import FrameResult
from app.session.analysis_session import AnalysisSession
from app.ui.analysis.widgets import (
    SourceGroup,
    ControlGroup,
    SettingsGroup,
    ClassesGroup,
    StatusGroup,
)


class AnalysisPage(QWidget):
    def __init__(
        self,
        session: AnalysisSession,
        available_videos: list[Path],
        default_video: str,
    ):
        super().__init__()

        self.analysis_session = session
        self.available_videos = available_videos
        self.default_video = default_video

        self.model_config = session.model_config
        self.default_confidence_threshold = session.confidence_threshold

        self.video_path: Optional[Path] = session.video_path
        self.current_display_frame = None

        self._clear_video_after_stop = True
        self._ignore_result_frames = False

        self._build_ui()
        self._connect_signals()
        self._connect_session_signals()
        self._update_control_states()

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        left_layout = QVBoxLayout()

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(920, 680)
        self.video_label.setObjectName("videoLabel")
        left_layout.addWidget(self.video_label)

        right_panel = QWidget()
        right_panel.setFixedWidth(380)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(14)

        self.source_group = SourceGroup(
            videos=self.available_videos,
            default_video=self.default_video,
        )

        self.control_group = ControlGroup()

        self.settings_group = SettingsGroup(
            confidence_threshold=self.default_confidence_threshold,
        )

        self.classes_group = ClassesGroup(self.model_config.classes)
        self.status_group = StatusGroup()

        right_layout.addWidget(self.source_group)
        right_layout.addWidget(self.control_group)
        right_layout.addWidget(self.settings_group)
        right_layout.addWidget(self.classes_group)
        right_layout.addWidget(self.status_group)
        right_layout.addStretch()

        root_layout.addLayout(left_layout, 1)
        root_layout.addWidget(right_panel)

        selected_video = self.source_group.selected_video_path()
        if selected_video:
            self._on_video_selected(selected_video)  

    def _connect_signals(self):
        self.source_group.video_selected.connect(self._on_video_selected)
        self.control_group.analysis_toggle_button.clicked.connect(self._toggle_analysis)
        self.control_group.pause_toggle_button.clicked.connect(self._toggle_pause)
        self.control_group.capture_button.clicked.connect(self._capture_frame)

        self.settings_group.conf_slider.valueChanged.connect(self._on_conf_changed)
        self.classes_group.selection_changed.connect(self._on_class_selection_changed)

    def _connect_session_signals(self):
        self.analysis_session.result_ready.connect(self._on_result_ready)
        self.analysis_session.status_changed.connect(self._on_status_changed)
        self.analysis_session.error_occurred.connect(self._on_error)
        self.analysis_session.session_started.connect(self._on_session_started)
        self.analysis_session.session_finished.connect(self._on_session_finished)

    def _update_control_states(self):
        video_selected = self.video_path is not None
        analysis_running = self.analysis_session.is_running()
        analysis_paused = self.analysis_session.is_paused()

        self.control_group.analysis_toggle_button.setEnabled(video_selected)

        self.control_group.analysis_toggle_button.setText(
            "Остановить анализ" if analysis_running else "Запустить анализ"
        )

        if analysis_running:
            self.control_group.pause_toggle_button.setEnabled(True)
            self.control_group.capture_button.setEnabled(True)
            self.control_group.pause_toggle_button.setText(
                "Продолжить" if analysis_paused else "Пауза"
            )
        else:
            self.control_group.pause_toggle_button.setEnabled(False)
            self.control_group.pause_toggle_button.setText("Пауза")
            self.control_group.capture_button.setEnabled(
                self.current_display_frame is not None
            )

    def _toggle_analysis(self):
        if self.analysis_session.is_running():
            self._clear_video_after_stop = True
            self._ignore_result_frames = True
            self.status_group.set_status("Завершение сеанса...")
            self.analysis_session.stop()
            self._update_control_states()
            return

        if not self.video_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите видео")
            return

        self._ignore_result_frames = False
        self.status_group.set_status("Запуск обработки")
        self.analysis_session.start()

    def _toggle_pause(self):
        if not self.analysis_session.is_running():
            return

        if self.analysis_session.is_paused():
            self.analysis_session.resume()
        else:
            self.analysis_session.pause()

        self._update_control_states()

    def _on_conf_changed(self, value: int):
        conf = value / 100.0
        self.settings_group.conf_value_label.setText(f"{conf:.2f}")
        self.analysis_session.set_confidence_threshold(conf)

    def _on_class_selection_changed(self, selected_ids: set[int]):
        self.analysis_session.set_enabled_class_ids(selected_ids)

    def _on_session_started(self):
        self._update_control_states()

    def _on_video_selected(self, video_path: Path) -> None:
        self.video_path = video_path
        self.analysis_session.change_video_path(video_path)
        self._update_control_states()

    def _on_session_finished(self):
        if self._clear_video_after_stop:
            self._clear_video_after_stop = False
            self._clear_video_display()

        self._ignore_result_frames = False
        self._update_control_states()

        if self.status_group.status_label.text() not in (
            "Ошибка",
            "Видео завершено",
            "Сеанс анализа завершён",
        ):
            self.status_group.set_status("Готово")

    def _on_result_ready(self, result: FrameResult):
        if self._ignore_result_frames:
            return

        self.current_display_frame = result.frame.copy()
        self._update_video(result.frame)
        self.status_group.update_metrics(
            detections_count=len(result.detections),
        )

    def _on_status_changed(self, text: str):
        self.status_group.set_status(text)
        self._update_control_states()

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)
        self.status_group.set_status("Ошибка")
        self._update_control_states()

    def _frame_to_pixmap(self, frame) -> QPixmap:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        bytes_per_line = channels * width
        image = QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(image)

    def _update_video(self, frame):
        pixmap = self._frame_to_pixmap(frame)
        scaled = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        pixmap = self.video_label.pixmap()
        if pixmap is not None:
            scaled = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.video_label.setPixmap(scaled)

    def _capture_frame(self):
        if self.current_display_frame is None:
            self.status_group.set_status("Нет кадра для сохранения")
            return

        try:
            self.analysis_session.capture_frame(self.current_display_frame)
            self._show_capture_success_feedback()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))

    def _show_capture_success_feedback(self):
        button = self.control_group.capture_button
        original_text = "Зафиксировать кадр"

        button.setText("Сохранено")
        button.setEnabled(False)

        QTimer.singleShot(1200, lambda: self._restore_capture_button(original_text))

    def _restore_capture_button(self, text: str):
        self.control_group.capture_button.setText(text)
        self.control_group.capture_button.setEnabled(
            self.analysis_session.is_running() or self.current_display_frame is not None
        )

    def _clear_video_display(self):
        self.current_display_frame = None
        self.video_label.clear()
