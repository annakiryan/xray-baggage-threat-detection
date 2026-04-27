import json
import logging
from dataclasses import asdict
from json import JSONDecodeError
from pathlib import Path

from app.domain.settings import InterfaceSettings


class InterfaceSettingsService:
    _logger = logging.getLogger(__name__)

    def __init__(self, settings_path: str | Path):
        self.settings_path = Path(settings_path)

    def load(self) -> InterfaceSettings:
        if not self.settings_path.exists():
            return InterfaceSettings()

        try:
            with self.settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            return InterfaceSettings(
                theme_key=data.get("theme_key", "dark"),
                ui_scale=int(data.get("ui_scale", 100)),
                bbox_color_key=data.get("bbox_color_key", "blue"),
                bbox_thickness=int(data.get("bbox_thickness", 2)),
            )

        except (OSError, JSONDecodeError, TypeError, ValueError) as exc:
            self._logger.warning(
                "Не удалось загрузить настройки интерфейса из %s: %s",
                self.settings_path,
                exc,
            )
            return InterfaceSettings()

    def save(self, settings: InterfaceSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(
                asdict(settings),
                f,
                ensure_ascii=False,
                indent=2,
            )
