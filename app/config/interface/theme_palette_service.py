import json
from pathlib import Path


class ThemePaletteService:
    @staticmethod
    def load(path: str | Path) -> dict:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Файл палитр не найден: {path}")

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
