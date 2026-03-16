from pathlib import Path
from typing import Any, List

import cv2
import numpy as np
import onnxruntime as ort

from app.domain.entities import ModelConfig


class OnnxDetector:
    def __init__(self, model_config: ModelConfig, device: str = "cpu"):
        self.model_config = model_config
        self.device = device.lower()
        self.session = None
        self.input_name = None
        self.output_names = None

        self._load_model()

    def _get_providers(self) -> list[str]:
        available_providers = ort.get_available_providers()

        if self.device == "cuda":
            if "CUDAExecutionProvider" in available_providers:
                return ["CUDAExecutionProvider", "CPUExecutionProvider"]
            return ["CPUExecutionProvider"]

        return ["CPUExecutionProvider"]

    def _load_model(self) -> None:
        model_path = Path(self.model_config.model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")

        providers = self._get_providers()

        self.session = ort.InferenceSession(
            str(model_path),
            providers=providers,
        )

        session_inputs = self.session.get_inputs()
        session_outputs = self.session.get_outputs()

        if not session_inputs:
            raise ValueError("У ONNX-модели отсутствуют входы")

        if not session_outputs:
            raise ValueError("У ONNX-модели отсутствуют выходы")

        self.input_name = self.model_config.input.input_name
        self.output_names = self.model_config.output.output_names

        real_input_names = [inp.name for inp in session_inputs]
        real_output_names = [out.name for out in session_outputs]

        if self.input_name not in real_input_names:
            raise ValueError(
                f"В конфиге указан input_name='{self.input_name}', "
                f"но в модели доступны входы: {real_input_names}"
            )

        for output_name in self.output_names:
            if output_name not in real_output_names:
                raise ValueError(
                    f"В конфиге указан output_name='{output_name}', "
                    f"но в модели доступны выходы: {real_output_names}"
                )

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        input_cfg = self.model_config.input

        resized = cv2.resize(frame, (input_cfg.width, input_cfg.height))

        if input_cfg.color_format.lower() == "rgb":
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        image = resized.astype(np.float32)

        if input_cfg.normalize:
            image = image / input_cfg.scale

        mean = np.array(input_cfg.mean, dtype=np.float32).reshape(1, 1, 3)
        std = np.array(input_cfg.std, dtype=np.float32).reshape(1, 1, 3)
        image = (image - mean) / std

        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)

        return image.astype(np.float32)

    def infer(self, input_tensor: np.ndarray) -> List[np.ndarray]:
        return self.session.run(
            self.output_names,
            {self.input_name: input_tensor},
        )

    def predict_raw(self, frame: np.ndarray) -> List[np.ndarray]:
        input_tensor = self.preprocess(frame)
        return self.infer(input_tensor)

    def get_runtime_info(self) -> dict[str, Any]:
        return {
            "device_requested": self.device,
            "available_providers": ort.get_available_providers(),
            "session_providers": self.session.get_providers(),
        }
