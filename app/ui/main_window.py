from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QScrollArea,
)

from app.core.worker import VideoProcessingWorker
from app.domain.entities import FrameResult, ModelConfig


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

        self.class_checkboxes: dict[int, QCheckBox] = {}
        self.enabled_class_ids = set(range(len(self.model_config.classes)))

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

        # =========================
        # Левая часть: видео
        # =========================
        left_layout = QVBoxLayout()

        self.video_label = QLabel("Видео не загружено")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(920, 680)
        self.video_label.setObjectName("videoLabel")

        left_layout.addWidget(self.video_label)

        # =========================
        # Правая часть: панель управления
        # =========================
        right_layout = QVBoxLayout()
        right_layout.setSpacing(14)

        # ---- Источник ----
        source_group = QGroupBox("Источник данных")
        source_form = QFormLayout()

        self.video_path_label = QLabel("Не выбрано")
        self.video_path_label.setWordWrap(True)

        self.open_video_button = QPushButton("Открыть видео")

        source_form.addRow("Файл:", self.video_path_label)
        source_form.addRow(self.open_video_button)
        source_group.setLayout(source_form)

        # ---- Управление ----
        control_group = QGroupBox("Управление обработкой")
        control_layout = QVBoxLayout()

        self.analysis_toggle_button = QPushButton("Запустить анализ")
        self.pause_toggle_button = QPushButton("Пауза")

        control_layout.addWidget(self.analysis_toggle_button)
        control_layout.addWidget(self.pause_toggle_button)
        control_group.setLayout(control_layout)

        # ---- Параметры ----
        settings_group = QGroupBox("Параметры инференса")
        settings_form = QFormLayout()

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(1, 100)
        self.conf_slider.setValue(int(self.default_confidence_threshold * 100))
        self.conf_value_label = QLabel(f"{self.default_confidence_threshold:.2f}")

        conf_widget = QWidget()
        conf_layout = QHBoxLayout(conf_widget)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        conf_layout.setSpacing(8)
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_value_label)

        self.iou_slider = QSlider(Qt.Horizontal)
        self.iou_slider.setRange(1, 100)
        self.iou_slider.setValue(int(self.default_iou_threshold * 100))
        self.iou_value_label = QLabel(f"{self.default_iou_threshold:.2f}")

        iou_widget = QWidget()
        iou_layout = QHBoxLayout(iou_widget)
        iou_layout.setContentsMargins(0, 0, 0, 0)
        iou_layout.setSpacing(8)
        iou_layout.addWidget(self.iou_slider)
        iou_layout.addWidget(self.iou_value_label)

        self.frame_skip_spin = QSpinBox()
        self.frame_skip_spin.setRange(1, 30)
        self.frame_skip_spin.setValue(self.default_frame_skip)

        settings_form.addRow("Confidence:", conf_widget)
        settings_form.addRow("IoU:", iou_widget)
        settings_form.addRow("Каждый N-й кадр:", self.frame_skip_spin)
        settings_group.setLayout(settings_form)

        # ---- Классы ----
        classes_group = QGroupBox("Отображаемые классы")
        classes_layout = QVBoxLayout()
        classes_layout.setContentsMargins(8, 8, 8, 8)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(6)

        for class_id, class_name in enumerate(self.model_config.classes):
            checkbox = QCheckBox(class_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_class_selection_changed)

            self.class_checkboxes[class_id] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        classes_layout.addWidget(scroll_area)
        classes_group.setLayout(classes_layout)
        classes_group.setMinimumHeight(240)

        # ---- Статус ----
        status_group = QGroupBox("Статус системы")
        status_form = QFormLayout()

        self.status_label = QLabel("Ожидание")
        self.model_label = QLabel(self.model_config.model_name)
        self.device_label = QLabel(self.device)
        self.fps_label = QLabel("-")
        self.inference_label = QLabel("-")
        self.detections_label = QLabel("0")

        status_form.addRow("Состояние:", self.status_label)
        status_form.addRow("Модель:", self.model_label)
        status_form.addRow("Устройство:", self.device_label)
        status_form.addRow("FPS:", self.fps_label)
        status_form.addRow("Инференс (мс):", self.inference_label)
        status_form.addRow("Детекций:", self.detections_label)
        status_group.setLayout(status_form)

        right_layout.addWidget(source_group)
        right_layout.addWidget(control_group)
        right_layout.addWidget(settings_group)
        right_layout.addWidget(classes_group)
        right_layout.addWidget(status_group)
        right_layout.addStretch()

        root_layout.addLayout(left_layout, 3)
        root_layout.addLayout(right_layout, 1)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #121417;
                color: #E6EAF0;
                font-size: 14px;
            }

            QGroupBox {
                background-color: #1A1F26;
                border: 1px solid #2A313B;
                border-radius: 12px;
                margin-top: 12px;
                padding: 12px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #DDE5F0;
            }

            QLabel {
                color: #E6EAF0;
            }

            QLabel#videoLabel {
                background-color: #0B0E12;
                border: 1px solid #2A313B;
                border-radius: 14px;
                color: #8E99A8;
                font-size: 18px;
            }

            QPushButton {
                background-color: #2B6BE4;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #3A78EC;
            }

            QPushButton:pressed {
                background-color: #2359C0;
            }

            QPushButton:disabled {
                background-color: #3A404A;
                color: #9199A6;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #2A313B;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #2B6BE4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSpinBox {
                background-color: #11161C;
                border: 1px solid #2A313B;
                border-radius: 8px;
                padding: 6px;
                color: #E6EAF0;
            }

            QCheckBox {
                spacing: 8px;
                padding: 4px 2px;
                color: #E6EAF0;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }

            QCheckBox::indicator:unchecked {
                border: 1px solid #4A5563;
                background: #11161C;
                border-radius: 4px;
            }

            QCheckBox::indicator:checked {
                border: 1px solid #2B6BE4;
                background: #2B6BE4;
                border-radius: 4px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }
        """
        )

    def _connect_signals(self):
        self.open_video_button.clicked.connect(self._choose_video)
        self.analysis_toggle_button.clicked.connect(self._toggle_analysis)
        self.pause_toggle_button.clicked.connect(self._toggle_pause)

        self.conf_slider.valueChanged.connect(self._on_conf_changed)
        self.iou_slider.valueChanged.connect(self._on_iou_changed)
        self.frame_skip_spin.valueChanged.connect(self._on_frame_skip_changed)

    def _update_control_states(self):
        video_selected = self.video_path is not None

        self.analysis_toggle_button.setEnabled(video_selected)

        if self.analysis_running:
            self.analysis_toggle_button.setText("Остановить анализ")
        else:
            self.analysis_toggle_button.setText("Запустить анализ")

        if self.analysis_running:
            self.pause_toggle_button.setEnabled(True)
            if self.analysis_paused:
                self.pause_toggle_button.setText("Продолжить")
            else:
                self.pause_toggle_button.setText("Пауза")
        else:
            self.pause_toggle_button.setEnabled(False)
            self.pause_toggle_button.setText("Пауза")

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
        self.video_path_label.setText(file_path)
        self.status_label.setText("Видео выбрано")
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
            confidence_threshold=self.conf_slider.value() / 100.0,
            iou_threshold=self.iou_slider.value() / 100.0,
            process_every_n_frames=self.frame_skip_spin.value(),
            draw_enabled=True,
        )

        self.worker.set_video_path(self.video_path)
        self.worker.set_enabled_class_ids(self.enabled_class_ids)
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
        self.status_label.setText("Запуск обработки")
        self._update_control_states()

    def _stop_processing(self):
        if self.worker is not None:
            self.worker.stop()

    def _on_conf_changed(self, value: int):
        conf = value / 100.0
        self.conf_value_label.setText(f"{conf:.2f}")

        if self.worker is not None:
            self.worker.set_confidence_threshold(conf)

    def _on_iou_changed(self, value: int):
        iou = value / 100.0
        self.iou_value_label.setText(f"{iou:.2f}")

        if self.worker is not None:
            self.worker.set_iou_threshold(iou)

    def _on_frame_skip_changed(self, value: int):
        if self.worker is not None:
            self.worker.set_process_every_n_frames(value)

    def _on_class_selection_changed(self):
        selected_ids = {
            class_id
            for class_id, checkbox in self.class_checkboxes.items()
            if checkbox.isChecked()
        }

        if not selected_ids:
            sender = self.sender()
            if sender is not None:
                sender.blockSignals(True)
                sender.setChecked(True)
                sender.blockSignals(False)

            QMessageBox.warning(
                self, "Предупреждение", "Должен быть выбран хотя бы один класс."
            )
            return

        self.enabled_class_ids = selected_ids

        if self.worker is not None:
            self.worker.set_enabled_class_ids(selected_ids)

    def _on_result_ready(self, result: FrameResult):
        self._update_video(result.frame)
        self.fps_label.setText(f"{result.fps:.2f}")
        self.inference_label.setText(f"{result.inference_time_ms:.2f}")
        self.detections_label.setText(str(len(result.detections)))

    def _on_status_changed(self, text: str):
        self.status_label.setText(text)

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)
        self.status_label.setText("Ошибка")

    def _on_worker_finished(self):
        self.worker = None
        self.worker_thread = None

        self.analysis_running = False
        self.analysis_paused = False

        self._update_control_states()

        if self.status_label.text() not in (
            "Ошибка",
            "Видео завершено",
            "Сеанс анализа завершён",
        ):
            self.status_label.setText("Готово")

    def _update_video(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)

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
