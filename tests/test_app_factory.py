import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.app_factory import build_dependencies


class AppFactoryTests(unittest.TestCase):
    def test_build_dependencies_loads_expected_objects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configs_dir = root / "configs"
            videos_dir = root / "videos"
            models_dir = root / "models"
            logs_dir = root / "logs"
            results_dir = root / "results"

            configs_dir.mkdir(parents=True)
            videos_dir.mkdir(parents=True)
            models_dir.mkdir(parents=True)
            logs_dir.mkdir(parents=True)
            results_dir.mkdir(parents=True)

            (videos_dir / "demo.mp4").write_bytes(b"video")

            app_config_path = configs_dir / "app_config.json"
            model_config_path = models_dir / "model_config.json"
            interface_settings_path = configs_dir / "interface_settings.json"
            theme_palettes_path = configs_dir / "theme_palettes.json"

            app_config = {
                "app_name": "Test app",
                "models_dir": str(models_dir),
                "model_config": "model_config.json",
                "videos_dir": str(videos_dir),
                "default_video": "demo.mp4",
                "logs_dir": str(logs_dir),
                "results_dir": str(results_dir),
                "default_confidence_threshold": 0.5,
                "default_iou_threshold": 0.45,
                "default_frame_skip": 2,
                "device": "cpu",
            }
            app_config_path.write_text(
                json.dumps(app_config, ensure_ascii=False),
                encoding="utf-8",
            )

            model_config = {
                "model_name": "dummy",
                "model_path": "dummy.onnx",
                "task_type": "detection",
                "input": {
                    "width": 640,
                    "height": 640,
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
                    "confidence_threshold": 0.25,
                    "iou_threshold": 0.45,
                    "max_detections": 300,
                },
                "classes": ["knife"],
            }
            model_config_path.write_text(
                json.dumps(model_config, ensure_ascii=False),
                encoding="utf-8",
            )

            interface_settings_path.write_text(
                json.dumps({"theme_key": "dark", "ui_scale": 110}, ensure_ascii=False),
                encoding="utf-8",
            )

            theme_palettes_path.write_text(
                json.dumps(
                    {
                        "dark": {"name": "Dark"},
                        "light": {"name": "Light"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch("app.app_factory.APP_CONFIG_PATH", app_config_path),
                patch(
                    "app.app_factory.INTERFACE_SETTINGS_PATH", interface_settings_path
                ),
                patch("app.app_factory.THEME_PALETTES_PATH", theme_palettes_path),
            ):
                deps = build_dependencies()

            self.assertEqual(deps.app_config.app_name, "Test app")
            self.assertEqual(deps.default_video_path, videos_dir / "demo.mp4")
            self.assertEqual(
                [path.name for path in deps.available_videos], ["demo.mp4"]
            )
            self.assertEqual(deps.model_config.model_name, "dummy")
            self.assertEqual(deps.interface_settings.ui_scale, 110)
            self.assertEqual(deps.theme_manager.get_palette("dark")["name"], "Dark")


if __name__ == "__main__":
    unittest.main()
