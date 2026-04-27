from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QComboBox,
)


class SettingsRow(QFrame):
    def __init__(self, icon: str, title: str, subtitle: str):
        super().__init__()
        self.setObjectName("settingsRow")

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(18)

        icon_label = QLabel(icon)
        icon_label.setObjectName("settingsIcon")
        icon_label.setFixedWidth(34)
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        title_label = QLabel(title)
        title_label.setObjectName("settingsRowTitle")
        title_label.setWordWrap(True)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("settingsRowSubtitle")
        subtitle_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        text_layout.addStretch()

        left = QWidget()
        left.setMinimumWidth(280)
        left.setMaximumWidth(330)
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)
        left_layout.addWidget(icon_label)
        left_layout.addLayout(text_layout)

        root = QHBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(26)
        root.addWidget(left)
        root.addLayout(self.content_layout, 1)


class ThemeCard(QPushButton):
    def __init__(self, key: str, name: str, palette: dict):
        super().__init__()
        self.key = key
        self.setCheckable(True)
        self.setObjectName("themeCard")
        self.setMinimumHeight(170)

        preview = ThemePreview(palette)

        title_label = QLabel(name)
        title_label.setObjectName("themeCardTitle")
        title_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(preview)
        layout.addWidget(title_label)


class ThemeSelector(SettingsRow):
    theme_changed = Signal(str)

    def __init__(
        self,
        options: list[tuple[str, str]],
        current_key: str,
        palettes: dict,
    ):
        super().__init__(
            icon="◉",
            title="Тема интерфейса",
            subtitle="Выберите визуальную тему приложения",
        )

        self.buttons: dict[str, ThemeCard] = {}

        for key, name in options:
            palette = palettes.get(key, palettes.get("dark", {}))

            button = ThemeCard(
                key=key,
                name=name,
                palette=palette,
            )
            button.setChecked(key == current_key)
            button.clicked.connect(lambda _, value=key: self._select_theme(value))

            self.buttons[key] = button
            self.content_layout.addWidget(button)

    def _select_theme(self, key: str):
        for button_key, button in self.buttons.items():
            button.setChecked(button_key == key)

        self.theme_changed.emit(key)


class ScaleSelector(SettingsRow):
    value_changed = Signal(int)

    def __init__(
        self,
        options: list[tuple[int, str]],
        current_value: int,
    ):
        super().__init__(
            icon="Aa",
            title="Масштаб интерфейса",
            subtitle="Измените размер элементов интерфейса",
        )

        self.values = [value for value, _ in options]

        self.minus_button = QPushButton("−")
        self.minus_button.setObjectName("scaleStepButton")
        self.minus_button.setFixedSize(56, 56)

        self.plus_button = QPushButton("+")
        self.plus_button.setObjectName("scaleStepButton")
        self.plus_button.setFixedSize(56, 56)

        self.combo = QComboBox()
        self.combo.setObjectName("scaleCombo")
        self.combo.setMinimumHeight(56)

        for value, label in options:
            self.combo.addItem(label, value)

        if current_value in self.values:
            self.combo.setCurrentIndex(self.values.index(current_value))
        else:
            self.combo.setCurrentIndex(0)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)
        controls_layout.addWidget(self.minus_button)
        controls_layout.addWidget(self.combo)
        controls_layout.addWidget(self.plus_button)
        controls_layout.addStretch()

        self.content_layout.addLayout(controls_layout)

        self.minus_button.clicked.connect(lambda: self._step(-1))
        self.plus_button.clicked.connect(lambda: self._step(1))
        self.combo.currentIndexChanged.connect(self._on_index_changed)

        self._update_buttons()

    def _step(self, delta: int):
        new_index = self.combo.currentIndex() + delta

        if 0 <= new_index < self.combo.count():
            self.combo.setCurrentIndex(new_index)

    def _on_index_changed(self, index: int):
        self._update_buttons()

        value = self.combo.itemData(index)
        if value is not None:
            self.value_changed.emit(int(value))

    def _update_buttons(self):
        index = self.combo.currentIndex()
        self.minus_button.setEnabled(index > 0)
        self.plus_button.setEnabled(index < self.combo.count() - 1)


class ColorCard(QPushButton):
    def __init__(self, key: str, title: str, color: str, subtitle: str = ""):
        super().__init__()
        self.key = key
        self.setCheckable(True)
        self.setObjectName("colorCard")
        self.setMinimumHeight(74)

        color_box = QLabel()
        color_box.setObjectName("colorPreview")
        color_box.setStyleSheet(f"background-color: {color};")
        color_box.setFixedSize(34, 34)

        title_label = QLabel(title)
        title_label.setObjectName("colorCardTitle")
        title_label.setWordWrap(True)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("colorCardSubtitle")
        subtitle_label.setWordWrap(True)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(12)
        row.addWidget(color_box)
        row.addWidget(title_label)
        row.addStretch()

    def setChecked(self, checked: bool):
        super().setChecked(checked)


class ColorSelector(SettingsRow):
    color_changed = Signal(str)

    def __init__(self, options: list[tuple[str, str, str]], current_key: str):
        super().__init__(
            icon="□",
            title="Цвет рамок детекции",
            subtitle="Выберите цвет рамок на изображении",
        )

        self.buttons: dict[str, ColorCard] = {}

        for key, title, color in options:
            subtitle = "По умолчанию" if key == "blue" else ""
            button = ColorCard(key, title, color, subtitle)
            button.setChecked(key == current_key)
            button.clicked.connect(lambda _, value=key: self._select_color(value))

            self.buttons[key] = button
            self.content_layout.addWidget(button)

    def _select_color(self, key: str):
        for button_key, button in self.buttons.items():
            button.setChecked(button_key == key)

        self.color_changed.emit(key)


class ThemePreview(QFrame):
    def __init__(self, palette: dict):
        super().__init__()
        self.setObjectName("themePreview")
        self.setMinimumHeight(120)

        bg_main = palette.get("bg_main", "#1E2227")
        bg_card = palette.get("bg_card", "#23272E")
        bg_inner = palette.get("bg_inner", "#1A1F26")
        border = palette.get("border", "#2A313B")
        accent = palette.get("accent", "#2B6BE4")

        back_panel = QFrame()
        back_panel.setObjectName("themePreviewBack")
        back_panel.setStyleSheet(
            f"""
            QFrame#themePreviewBack {{
                background-color: {bg_main};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            """
        )

        top_line = QFrame()
        top_line.setObjectName("themePreviewLine")
        top_line.setMinimumHeight(14)
        top_line.setStyleSheet(
            f"""
            QFrame#themePreviewLine {{
                background-color: {accent};
                border-radius: 4px;
            }}
            """
        )

        short_line = QFrame()
        short_line.setObjectName("themePreviewShortLine")
        short_line.setFixedSize(72, 14)
        short_line.setStyleSheet(
            f"""
            QFrame#themePreviewShortLine {{
                background-color: {border};
                border-radius: 4px;
            }}
            """
        )

        content_panel = QFrame()
        content_panel.setObjectName("themePreviewContent")
        content_panel.setStyleSheet(
            f"""
            QFrame#themePreviewContent {{
                background-color: {bg_card};
                border-radius: 6px;
            }}
            """
        )

        small_panel = QFrame()
        small_panel.setMinimumHeight(14)
        small_panel.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg_inner};
                border-radius: 4px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        inner_layout = QVBoxLayout(back_panel)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(8)

        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)
        content_layout.addWidget(short_line, alignment=Qt.AlignLeft)
        content_layout.addWidget(small_panel)
        content_layout.addStretch()

        inner_layout.addWidget(top_line)
        inner_layout.addWidget(content_panel)

        layout.addWidget(back_panel)


class ThicknessPreview(QFrame):
    def __init__(self, thickness: int):
        super().__init__()
        self.setObjectName("thicknessPreview")
        self.setFixedSize(80, 36)

        line = QFrame()
        line.setObjectName("thicknessLine")
        line.setFixedSize(52, thickness)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch()
        row.addWidget(line)
        row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addLayout(row)
        layout.addStretch()


class ThicknessButton(QPushButton):
    def __init__(self, value: int):
        super().__init__()
        self.value = value
        self.setCheckable(True)
        self.setObjectName("thicknessButton")

        self.setMinimumHeight(68)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        preview = ThicknessPreview(value)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(preview, alignment=Qt.AlignCenter)
        layout.addStretch()


class ThicknessSelector(SettingsRow):
    value_changed = Signal(int)

    def __init__(self, values: list[int], current_value: int):
        super().__init__(
            icon="☷",
            title="Толщина рамок детекции",
            subtitle="Настройте толщину рамок на изображении",
        )

        self.buttons: dict[int, ThicknessButton] = {}

        for value in values:
            button = ThicknessButton(value)
            button.setChecked(value == current_value)
            button.clicked.connect(lambda _, v=value: self._select_value(v))

            self.buttons[value] = button
            self.content_layout.addWidget(button)

    def _select_value(self, value: int):
        for button_value, button in self.buttons.items():
            button.setChecked(button_value == value)

        self.value_changed.emit(value)
