import json

import pytest

from app.config.model.model_config_service import ModelConfigService


def make_valid_model_config() -> dict:
    return {
        "model_name": "xray_yolo",
        "model_path": "models/xray_yolo/model.onnx",
        "task_type": "detection",
        "input": {
            "width": 1024,
            "height": 1024,
            "channels": 3,
            "input_name": "images",
            "color_format": "rgb",
            "normalize": True,
            "scale": 255.0,
            "mean": [0.0, 0.0, 0.0],
            "std": [1.0, 1.0, 1.0],
        },
        "output": {
            "output_names": ["output0"],
            "format": "yolo",
        },
        "postprocess": {
            "confidence_threshold": 0.4,
            "iou_threshold": 0.5,
            "max_detections": 100,
        },
        "classes": ["gun", "knife"],
    }


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def test_load_model_config_reads_valid_config(tmp_path):
    config_path = tmp_path / "model_config.json"
    write_json(config_path, make_valid_model_config())

    config = ModelConfigService.load_model_config(config_path)

    assert config.model_name == "xray_yolo"
    assert config.model_path == "models/xray_yolo/model.onnx"
    assert config.task_type == "detection"

    assert config.input.width == 1024
    assert config.input.height == 1024
    assert config.input.channels == 3
    assert config.input.input_name == "images"
    assert config.input.color_format == "rgb"
    assert config.input.normalize is True
    assert config.input.scale == 255.0
    assert config.input.mean == [0.0, 0.0, 0.0]
    assert config.input.std == [1.0, 1.0, 1.0]

    assert config.output.output_names == ["output0"]
    assert config.output.format == "yolo"

    assert config.postprocess.confidence_threshold == 0.4
    assert config.postprocess.iou_threshold == 0.5
    assert config.postprocess.max_detections == 100

    assert config.classes == ["gun", "knife"]


def test_load_model_config_raises_if_file_does_not_exist(tmp_path):
    config_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        ModelConfigService.load_model_config(config_path)


def test_load_model_config_raises_if_file_is_not_json(tmp_path):
    config_path = tmp_path / "model_config.txt"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Ожидался JSON-файл"):
        ModelConfigService.load_model_config(config_path)


def test_load_model_config_raises_if_root_is_not_object(tmp_path):
    config_path = tmp_path / "model_config.json"
    write_json(config_path, ["not", "object"])

    with pytest.raises(ValueError, match="ожидался объект"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "model_name",
        "model_path",
        "task_type",
        "input",
        "output",
        "postprocess",
        "classes",
    ],
)
def test_load_model_config_raises_if_required_top_level_field_is_missing(
    tmp_path,
    field_name,
):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data.pop(field_name)

    write_json(config_path, data)

    with pytest.raises(ValueError, match="отсутствуют обязательные поля"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "width",
        "height",
        "channels",
        "input_name",
        "color_format",
        "normalize",
        "scale",
        "mean",
        "std",
    ],
)
def test_load_model_config_raises_if_required_input_field_is_missing(
    tmp_path,
    field_name,
):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["input"].pop(field_name)

    write_json(config_path, data)

    with pytest.raises(ValueError, match="В блоке input отсутствует поле"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "output_names",
        "format",
    ],
)
def test_load_model_config_raises_if_required_output_field_is_missing(
    tmp_path,
    field_name,
):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["output"].pop(field_name)

    write_json(config_path, data)

    with pytest.raises(ValueError, match="В блоке output отсутствует поле"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "field_name",
    [
        "confidence_threshold",
        "iou_threshold",
        "max_detections",
    ],
)
def test_load_model_config_raises_if_required_postprocess_field_is_missing(
    tmp_path,
    field_name,
):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["postprocess"].pop(field_name)

    write_json(config_path, data)

    with pytest.raises(ValueError, match="В блоке postprocess отсутствует поле"):
        ModelConfigService.load_model_config(config_path)


def test_load_model_config_raises_if_classes_is_empty(tmp_path):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["classes"] = []

    write_json(config_path, data)

    with pytest.raises(ValueError, match="classes"):
        ModelConfigService.load_model_config(config_path)


def test_load_model_config_raises_if_classes_is_not_list(tmp_path):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["classes"] = "gun"

    write_json(config_path, data)

    with pytest.raises(ValueError, match="classes"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "value",
    [-0.1, 1.1],
)
def test_load_model_config_raises_if_confidence_threshold_out_of_range(
    tmp_path,
    value,
):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["postprocess"]["confidence_threshold"] = value

    write_json(config_path, data)

    with pytest.raises(ValueError, match="confidence_threshold"):
        ModelConfigService.load_model_config(config_path)


@pytest.mark.parametrize(
    "value",
    [-0.1, 1.1],
)
def test_load_model_config_raises_if_iou_threshold_out_of_range(tmp_path, value):
    config_path = tmp_path / "model_config.json"
    data = make_valid_model_config()
    data["postprocess"]["iou_threshold"] = value

    write_json(config_path, data)

    with pytest.raises(ValueError, match="iou_threshold"):
        ModelConfigService.load_model_config(config_path)
