import json

from app.config.interface.interface_settings_service import InterfaceSettingsService
from app.domain.settings import InterfaceSettings


def test_load_returns_default_settings_if_file_does_not_exist(tmp_path):
    settings_path = tmp_path / "interface_settings.json"
    service = InterfaceSettingsService(settings_path)

    settings = service.load()

    assert settings == InterfaceSettings()


def test_save_creates_settings_file(tmp_path):
    settings_path = tmp_path / "configs" / "interface_settings.json"
    service = InterfaceSettingsService(settings_path)

    settings = InterfaceSettings(
        theme_key="light",
        ui_scale=110,
        bbox_color_key="green",
        bbox_thickness=4,
    )

    service.save(settings)

    assert settings_path.exists()


def test_save_writes_settings_to_json(tmp_path):
    settings_path = tmp_path / "interface_settings.json"
    service = InterfaceSettingsService(settings_path)

    settings = InterfaceSettings(
        theme_key="light",
        ui_scale=115,
        bbox_color_key="yellow",
        bbox_thickness=5,
    )

    service.save(settings)

    with settings_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == {
        "theme_key": "light",
        "ui_scale": 115,
        "bbox_color_key": "yellow",
        "bbox_thickness": 5,
    }


def test_load_reads_settings_from_json(tmp_path):
    settings_path = tmp_path / "interface_settings.json"

    settings_path.write_text(
        json.dumps(
            {
                "theme_key": "light",
                "ui_scale": 120,
                "bbox_color_key": "red",
                "bbox_thickness": 6,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = InterfaceSettingsService(settings_path)

    settings = service.load()

    assert settings.theme_key == "light"
    assert settings.ui_scale == 120
    assert settings.bbox_color_key == "red"
    assert settings.bbox_thickness == 6


def test_load_uses_defaults_for_missing_fields(tmp_path):
    settings_path = tmp_path / "interface_settings.json"

    settings_path.write_text(
        json.dumps(
            {
                "theme_key": "light",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = InterfaceSettingsService(settings_path)

    settings = service.load()

    assert settings.theme_key == "light"
    assert settings.ui_scale == 100
    assert settings.bbox_color_key == "blue"
    assert settings.bbox_thickness == 2


def test_load_returns_default_settings_if_json_is_broken(tmp_path):
    settings_path = tmp_path / "interface_settings.json"
    settings_path.write_text("{ broken json", encoding="utf-8")

    service = InterfaceSettingsService(settings_path)

    settings = service.load()

    assert settings == InterfaceSettings()


def test_load_returns_default_settings_if_value_type_is_invalid(tmp_path):
    settings_path = tmp_path / "interface_settings.json"

    settings_path.write_text(
        json.dumps(
            {
                "theme_key": "dark",
                "ui_scale": "big",
                "bbox_color_key": "blue",
                "bbox_thickness": 2,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = InterfaceSettingsService(settings_path)

    settings = service.load()

    assert settings == InterfaceSettings()
