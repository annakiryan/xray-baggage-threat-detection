from typing import Protocol

from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel

from app.config.interface.interface_settings_service import InterfaceSettingsService
from app.domain.settings import (
    InterfaceSettings,
    UI_SCALE_OPTIONS,
    BBOX_COLOR_OPTIONS,
    BBOX_THICKNESS_OPTIONS,
)
from app.ui.settings.widgets import (
    ThemeSelector,
    ScaleSelector,
    ColorSelector,
    ThicknessSelector,
)
from PySide6.QtCore import Signal


class ThemeManagerProtocol(Protocol):
    def get_theme_options(self) -> list[tuple[str, str]]: ...

    def get_palettes(self) -> dict[str, dict]: ...


class SettingsPage(QWidget):
    theme_changed = Signal(str)
    ui_scale_changed = Signal(int)
    bbox_color_changed = Signal(str)
    bbox_thickness_changed = Signal(int)

    def __init__(
        self,
        settings: InterfaceSettings,
        settings_service: InterfaceSettingsService,
        theme_manager: ThemeManagerProtocol,
    ):
        super().__init__()

        self.theme_manager = theme_manager
        self.settings = settings
        self.settings_service = settings_service

        self.setObjectName("settingsPageRoot")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(18)

        title = QLabel("Настройки")
        title.setObjectName("settingsPageTitle")

        self.theme_selector = ThemeSelector(
            options=self.theme_manager.get_theme_options(),
            current_key=self.settings.theme_key,
            palettes=self.theme_manager.get_palettes(),
        )

        self.ui_scale_selector = ScaleSelector(
            options=UI_SCALE_OPTIONS,
            current_value=self.settings.ui_scale,
        )

        self.color_selector = ColorSelector(
            options=BBOX_COLOR_OPTIONS,
            current_key=self.settings.bbox_color_key,
        )

        self.bbox_thickness_selector = ThicknessSelector(
            values=BBOX_THICKNESS_OPTIONS,
            current_value=self.settings.bbox_thickness,
        )

        root.addWidget(title)
        root.addSpacing(24)
        root.addWidget(self.theme_selector)
        root.addWidget(self.ui_scale_selector)
        root.addWidget(self.color_selector)
        root.addWidget(self.bbox_thickness_selector)
        root.addStretch()

    def _connect_signals(self):
        self.theme_selector.theme_changed.connect(self._on_theme_changed)
        self.ui_scale_selector.value_changed.connect(self._on_ui_scale_changed)
        self.color_selector.color_changed.connect(self._on_bbox_color_changed)
        self.bbox_thickness_selector.value_changed.connect(
            self._on_bbox_thickness_changed
        )

    def _on_theme_changed(self, theme_key: str):
        self.settings.theme_key = theme_key
        self._save_settings()
        self.theme_changed.emit(theme_key)

    def _on_ui_scale_changed(self, value: int):
        self.settings.ui_scale = value
        self._save_settings()
        self.ui_scale_changed.emit(value)

    def _on_bbox_color_changed(self, color_key: str):
        self.settings.bbox_color_key = color_key
        self._save_settings()
        self.bbox_color_changed.emit(color_key)

    def _on_bbox_thickness_changed(self, value: int):
        self.settings.bbox_thickness = value
        self._save_settings()
        self.bbox_thickness_changed.emit(value)

    def _save_settings(self):
        self.settings_service.save(self.settings)
