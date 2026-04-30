import json

import pytest

from app.config.app.app_config_service import ConfigService


def make_valid_app_config() -> dict:
    return {
        "app_name": "XRay Dangerous Object Detection",
        "models_dir": "models",
        "model_config": "xray_yolo/config.json",
        "videos_dir": "data/videos",
        "default_video": "video.mp4",
        "logs_dir": "logs",
        "results_dir": "results",
        "default_confidence_threshold": 0.8,
        "default_iou_threshold": 0.2,
        "default_frame_skip": 1,
        "device": "cpu",
    }


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def test_load_app_config_reads_valid_config(tmp_path):
    config_path = tmp_path / "app_config.json"
    write_json(config_path, make_valid_app_config())

    config = ConfigService.load_app_config(config_path)

    assert config.app_name == "XRay Dangerous Object Detection"
    assert config.models_dir == "models"
    assert config.model_config == "xray_yolo/config.json"
    assert config.videos_dir == "data/videos"
    assert config.default_video == "video.mp4"
    assert config.logs_dir == "logs"
    assert config.results_dir == "results"
    assert config.default_confidence_threshold == 0.8
    assert config.default_iou_threshold == 0.2
    assert config.default_frame_skip == 1
    assert config.device == "cpu"


def test_load_app_config_raises_if_file_does_not_exist(tmp_path):
    config_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        ConfigService.load_app_config(config_path)


def test_load_app_config_raises_if_file_is_not_json(tmp_path):
    config_path = tmp_path / "app_config.txt"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Ожидался JSON-файл"):
        ConfigService.load_app_config(config_path)


def test_load_app_config_raises_if_root_is_not_object(tmp_path):
    config_path = tmp_path / "app_config.json"
    write_json(config_path, ["not", "object"])

    with pytest.raises(ValueError, match="ожидался объект"):
        ConfigService.load_app_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "app_name",
        "models_dir",
        "model_config",
        "videos_dir",
        "default_video",
        "logs_dir",
        "results_dir",
        "default_confidence_threshold",
        "default_iou_threshold",
        "default_frame_skip",
        "device",
    ],
)
def test_load_app_config_raises_if_required_field_is_missing(tmp_path, field_name):
    config_path = tmp_path / "app_config.json"
    data = make_valid_app_config()
    data.pop(field_name)

    write_json(config_path, data)

    with pytest.raises(ValueError, match="отсутствуют обязательные поля"):
        ConfigService.load_app_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "app_name",
        "models_dir",
        "model_config",
        "videos_dir",
        "default_video",
        "logs_dir",
        "results_dir",
        "device",
    ],
)
def test_load_app_config_raises_if_string_field_is_empty(tmp_path, field_name):
    config_path = tmp_path / "app_config.json"
    data = make_valid_app_config()
    data[field_name] = "   "

    write_json(config_path, data)

    with pytest.raises(ValueError):
        ConfigService.load_app_config(config_path)


@pytest.mark.parametrize(
    "value",
    [-0.1, 1.1],
)
def test_load_app_config_raises_if_confidence_threshold_out_of_range(tmp_path, value):
    config_path = tmp_path / "app_config.json"
    data = make_valid_app_config()
    data["default_confidence_threshold"] = value

    write_json(config_path, data)

    with pytest.raises(ValueError, match="default_confidence_threshold"):
        ConfigService.load_app_config(config_path)


@pytest.mark.parametrize(
    "value",
    [-0.1, 1.1],
)
def test_load_app_config_raises_if_iou_threshold_out_of_range(tmp_path, value):
    config_path = tmp_path / "app_config.json"
    data = make_valid_app_config()
    data["default_iou_threshold"] = value

    write_json(config_path, data)

    with pytest.raises(ValueError, match="default_iou_threshold"):
        ConfigService.load_app_config(config_path)


def test_load_app_config_raises_if_frame_skip_less_than_one(tmp_path):
    config_path = tmp_path / "app_config.json"
    data = make_valid_app_config()
    data["default_frame_skip"] = 0

    write_json(config_path, data)

    with pytest.raises(ValueError, match="default_frame_skip"):
        ConfigService.load_app_config(config_path)
