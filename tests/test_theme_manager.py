import pytest

from app.config.interface.theme_manager import ThemeManager


def test_get_palette_returns_requested_palette():
    palettes = {
        "dark": {"name": "Тёмная", "bg_main": "#000000"},
        "light": {"name": "Светлая", "bg_main": "#FFFFFF"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_palette("light") == {
        "name": "Светлая",
        "bg_main": "#FFFFFF",
    }


def test_get_palette_returns_dark_palette_if_requested_key_missing():
    palettes = {
        "dark": {"name": "Тёмная", "bg_main": "#000000"},
        "light": {"name": "Светлая", "bg_main": "#FFFFFF"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_palette("unknown") == {
        "name": "Тёмная",
        "bg_main": "#000000",
    }


def test_get_palette_returns_first_palette_if_dark_palette_missing():
    palettes = {
        "blue": {"name": "Синяя", "bg_main": "#001122"},
        "light": {"name": "Светлая", "bg_main": "#FFFFFF"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_palette("unknown") == {
        "name": "Синяя",
        "bg_main": "#001122",
    }


def test_get_palette_raises_if_palette_list_is_empty():
    manager = ThemeManager({})

    with pytest.raises(ValueError, match="Список палитр пуст"):
        manager.get_palette("dark")


def test_get_theme_options_returns_key_and_display_name():
    palettes = {
        "dark": {"name": "Тёмная"},
        "light": {"name": "Светлая"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_theme_options() == [
        ("dark", "Тёмная"),
        ("light", "Светлая"),
    ]


def test_get_theme_options_uses_key_if_name_is_missing():
    palettes = {
        "custom": {"bg_main": "#000000"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_theme_options() == [
        ("custom", "custom"),
    ]


def test_get_palettes_returns_original_palettes():
    palettes = {
        "dark": {"name": "Тёмная"},
    }

    manager = ThemeManager(palettes)

    assert manager.get_palettes() is palettes
