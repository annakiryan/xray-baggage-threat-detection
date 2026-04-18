from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from app.processing.worker import VideoProcessingWorker
from app.domain.entities import FrameResult, ModelConfig
from app.video.capture_service import CaptureService
from app.ui.styles import MAIN_WINDOW_STYLE
from app.ui.widgets import (
    SourceGroup,
    ControlGroup,
    SettingsGroup,
    ClassesGroup,
    StatusGroup,
)


class MainWindow(QMainWindow):
    def __init__(
        self,
        model_config: ModelConfig,
        device: str = "cpu",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        frame_skip: int = 1,
    ):
        super().__init__()

        self.model_config = model_config
        self.device = device
        self.default_confidence_threshold = confidence_threshold
        self.default_iou_threshold = iou_threshold
        self.default_frame_skip = frame_skip

        self.video_path: Optional[str] = None
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[VideoProcessingWorker] = None
        self.current_display_frame = None

        self.analysis_running = False
        self.analysis_paused = False

        self.setWindowTitle("XRay Dangerous Object Detection")
        self.resize(1450, 880)

        self._build_ui()
        self._apply_styles()
        self._connect_signals()
        self._update_control_states()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        left_layout = QVBoxLayout()
        self.video_label = QLabel("Видео не загружено")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(920, 680)
        self.video_label.setObjectName("videoLabel")
        left_layout.addWidget(self.video_label)

        right_panel = QWidget()
        right_panel.setFixedWidth(380)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(14)

        self.source_group = SourceGroup()
        self.control_group = ControlGroup()
        self.settings_group = SettingsGroup(
            confidence_threshold=self.default_confidence_threshold,
            iou_threshold=self.default_iou_threshold,
            frame_skip=self.default_frame_skip,
        )
        self.classes_group = ClassesGroup(self.model_config.classes)
        self.status_group = StatusGroup(
            model_name=self.model_config.model_name,
            device=self.device,
        )

        right_layout.addWidget(self.source_group)
        right_layout.addWidget(self.control_group)
        right_layout.addWidget(self.settings_group)
        right_layout.addWidget(self.classes_group)
        right_layout.addWidget(self.status_group)
        right_layout.addStretch()

        root_layout.addLayout(left_layout, 1)
        root_layout.addWidget(right_panel)

    def _apply_styles(self):
        self.setStyleSheet(MAIN_WINDOW_STYLE)

    def _connect_signals(self):
        self.source_group.open_video_button.clicked.connect(self._choose_video)
        self.control_group.analysis_toggle_button.clicked.connect(self._toggle_analysis)
        self.control_group.pause_toggle_button.clicked.connect(self._toggle_pause)
        self.control_group.capture_button.clicked.connect(self._capture_frame)

        self.settings_group.conf_slider.valueChanged.connect(self._on_conf_changed)
        self.settings_group.iou_slider.valueChanged.connect(self._on_iou_changed)
        self.settings_group.frame_skip_spin.valueChanged.connect(
            self._on_frame_skip_changed
        )

        self.classes_group.selection_changed.connect(self._on_class_selection_changed)

    def _update_control_states(self):
        video_selected = self.video_path is not None

        self.control_group.analysis_toggle_button.setEnabled(video_selected)

        if self.analysis_running:
            self.control_group.analysis_toggle_button.setText("Остановить анализ")
        else:
            self.control_group.analysis_toggle_button.setText("Запустить анализ")

        if self.analysis_running:
            self.control_group.pause_toggle_button.setEnabled(True)
            self.control_group.capture_button.setEnabled(True)

            if self.analysis_paused:
                self.control_group.pause_toggle_button.setText("Продолжить")
            else:
                self.control_group.pause_toggle_button.setText("Пауза")
        else:
            self.control_group.pause_toggle_button.setEnabled(False)
            self.control_group.pause_toggle_button.setText("Пауза")
            self.control_group.capture_button.setEnabled(
                self.current_display_frame is not None
            )

    def _choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите видео",
            str(Path.cwd()),
            "Video Files (*.mp4 *.avi *.mov *.mkv)",
        )

        if not file_path:
            return

        self.video_path = file_path
        self.source_group.video_path_label.setText(file_path)
        self.status_group.set_status("Видео выбрано")
        self._update_control_states()

    def _toggle_analysis(self):
        if not self.analysis_running:
            self._start_processing()
        else:
            self._stop_processing()

    def _toggle_pause(self):
        if not self.analysis_running or self.worker is None:
            return

        if not self.analysis_paused:
            self.worker.pause()
            self.analysis_paused = True
        else:
            self.worker.resume()
            self.analysis_paused = False

        self._update_control_states()

    def _start_processing(self):
        if not self.video_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите видео")
            return

        if self.worker_thread is not None:
            QMessageBox.information(self, "Информация", "Обработка уже запущена")
            return

        self.worker_thread = QThread()
        self.worker = VideoProcessingWorker(
            model_config=self.model_config,
            device=self.device,
            confidence_threshold=self.settings_group.conf_slider.value() / 100.0,
            iou_threshold=self.settings_group.iou_slider.value() / 100.0,
            process_every_n_frames=self.settings_group.frame_skip_spin.value(),
            draw_enabled=True,
        )

        self.worker.set_video_path(self.video_path)
        self.worker.set_enabled_class_ids(self.classes_group.get_enabled_class_ids())
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.start)
        self.worker.result_ready.connect(self._on_result_ready)
        self.worker.status_changed.connect(self._on_status_changed)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

        self.analysis_running = True
        self.analysis_paused = False
        self.status_group.set_status("Запуск обработки")
        self._update_control_states()

    def _stop_processing(self):
        if self.worker is not None:
            self.worker.stop()

    def _on_conf_changed(self, value: int):
        conf = value / 100.0
        self.settings_group.conf_value_label.setText(f"{conf:.2f}")

        if self.worker is not None:
            self.worker.set_confidence_threshold(conf)

    def _on_iou_changed(self, value: int):
        iou = value / 100.0
        self.settings_group.iou_value_label.setText(f"{iou:.2f}")

        if self.worker is not None:
            self.worker.set_iou_threshold(iou)

    def _on_frame_skip_changed(self, value: int):
        if self.worker is not None:
            self.worker.set_process_every_n_frames(value)

    def _on_class_selection_changed(self, selected_ids: set[int]):
        if not selected_ids:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Должен быть выбран хотя бы один класс.",
            )
            return

        if self.worker is not None:
            self.worker.set_enabled_class_ids(selected_ids)

    def _on_result_ready(self, result: FrameResult):
        self.current_display_frame = result.frame.copy()
        self._update_video(result.frame)
        self.status_group.update_metrics(
            fps=result.fps,
            inference_time_ms=result.inference_time_ms,
            detections_count=len(result.detections),
        )

    def _on_status_changed(self, text: str):
        self.status_group.set_status(text)

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)
        self.status_group.set_status("Ошибка")

    def _on_worker_finished(self):
        self.worker = None
        self.worker_thread = None

        self.analysis_running = False
        self.analysis_paused = False

        self._update_control_states()

        if self.status_group.status_label.text() not in (
            "Ошибка",
            "Видео завершено",
            "Сеанс анализа завершён",
        ):
            self.status_group.set_status("Готово")

    def _frame_to_pixmap(self, frame) -> QPixmap:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
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
            save_path = CaptureService.save_frame(
                self.current_display_frame,
                results_dir="results",
            )

            self.status_group.set_status(f"Кадр сохранён: {Path(save_path).name}")
            self._show_capture_success_feedback()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
            self.status_group.set_status("Ошибка сохранения кадра")

    def _show_capture_success_feedback(self):
        button = self.control_group.capture_button
        original_text = "Зафиксировать кадр"

        button.setText("Сохранено")
        button.setEnabled(False)

        QTimer.singleShot(1200, lambda: self._restore_capture_button(original_text))

    def _restore_capture_button(self, text: str):
        self.control_group.capture_button.setText(text)
        self.control_group.capture_button.setEnabled(
            self.analysis_running or self.current_display_frame is not None
        )
