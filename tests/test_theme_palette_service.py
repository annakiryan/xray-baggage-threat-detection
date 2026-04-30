import json

import pytest

from app.config.interface.theme_palette_service import ThemePaletteService


def test_load_reads_theme_palettes_from_json(tmp_path):
    palettes_path = tmp_path / "theme_palettes.json"

    palettes = {
        "dark": {
            "name": "Тёмная",
            "bg_main": "#111111",
            "text": "#FFFFFF",
        },
        "light": {
            "name": "Светлая",
            "bg_main": "#FFFFFF",
            "text": "#111111",
        },
    }

    palettes_path.write_text(
        json.dumps(palettes, ensure_ascii=False),
        encoding="utf-8",
    )

    result = ThemePaletteService.load(palettes_path)

    assert result == palettes


def test_load_raises_if_file_does_not_exist(tmp_path):
    palettes_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Файл палитр не найден"):
        ThemePaletteService.load(palettes_path)


def test_load_raises_if_json_is_invalid(tmp_path):
    palettes_path = tmp_path / "theme_palettes.json"
    palettes_path.write_text("{ broken json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        ThemePaletteService.load(palettes_path)
