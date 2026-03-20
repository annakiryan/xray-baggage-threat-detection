from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SourceGroup(QGroupBox):
    def __init__(self):
        super().__init__("Источник данных")

        self.video_path_label = QLabel("Не выбрано")
        self.video_path_label.setWordWrap(True)

        self.open_video_button = QPushButton("Открыть видео")

        form = QFormLayout()
        form.addRow("Файл:", self.video_path_label)
        form.addRow(self.open_video_button)
        self.setLayout(form)


class ControlGroup(QGroupBox):
    def __init__(self):
        super().__init__("Управление обработкой")

        self.analysis_toggle_button = QPushButton("Запустить анализ")
        self.pause_toggle_button = QPushButton("Пауза")
        self.capture_button = QPushButton("Зафиксировать кадр")
        self.capture_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.analysis_toggle_button)
        layout.addWidget(self.pause_toggle_button)
        layout.addWidget(self.capture_button)
        self.setLayout(layout)


class SettingsGroup(QGroupBox):
    def __init__(
        self,
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.5,
        frame_skip: int = 1,
    ):
        super().__init__("Параметры инференса")

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(1, 100)
        self.conf_slider.setValue(int(confidence_threshold * 100))
        self.conf_value_label = QLabel(f"{confidence_threshold:.2f}")

        conf_widget = QWidget()
        conf_layout = QHBoxLayout(conf_widget)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        conf_layout.setSpacing(8)
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_value_label)

        self.iou_slider = QSlider(Qt.Horizontal)
        self.iou_slider.setRange(1, 100)
        self.iou_slider.setValue(int(iou_threshold * 100))
        self.iou_value_label = QLabel(f"{iou_threshold:.2f}")

        iou_widget = QWidget()
        iou_layout = QHBoxLayout(iou_widget)
        iou_layout.setContentsMargins(0, 0, 0, 0)
        iou_layout.setSpacing(8)
        iou_layout.addWidget(self.iou_slider)
        iou_layout.addWidget(self.iou_value_label)

        self.frame_skip_spin = QSpinBox()
        self.frame_skip_spin.setRange(1, 30)
        self.frame_skip_spin.setValue(frame_skip)

        form = QFormLayout()
        form.addRow("Confidence:", conf_widget)
        form.addRow("IoU:", iou_widget)
        form.addRow("Каждый N-й кадр:", self.frame_skip_spin)
        self.setLayout(form)


class ClassesGroup(QGroupBox):
    selection_changed = Signal(set)

    def __init__(self, class_names: list[str]):
        super().__init__("Отображаемые классы")

        self.class_checkboxes: dict[int, QCheckBox] = {}
        self.enabled_class_ids = set(range(len(class_names)))

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(6)

        for class_id, class_name in enumerate(class_names):
            checkbox = QCheckBox(class_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_state_changed)

            self.class_checkboxes[class_id] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        self.setLayout(layout)
        self.setMinimumHeight(240)

    def _on_state_changed(self):
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
            return

        self.enabled_class_ids = selected_ids
        self.selection_changed.emit(selected_ids)

    def get_enabled_class_ids(self) -> set[int]:
        return set(self.enabled_class_ids)


class StatusGroup(QGroupBox):
    def __init__(self, model_name: str, device: str):
        super().__init__("Статус системы")

        self.status_label = QLabel("Ожидание")
        self.model_label = QLabel(model_name)
        self.device_label = QLabel(device)
        self.fps_label = QLabel("-")
        self.inference_label = QLabel("-")
        self.detections_label = QLabel("0")

        form = QFormLayout()
        form.addRow("Состояние:", self.status_label)
        form.addRow("Детекций:", self.detections_label)
        self.setLayout(form)

    def update_metrics(
        self, fps: float, inference_time_ms: float, detections_count: int
    ):
        self.fps_label.setText(f"{fps:.2f}")
        self.inference_label.setText(f"{inference_time_ms:.2f}")
        self.detections_label.setText(str(detections_count))

    def set_status(self, text: str):
        self.status_label.setText(text)
