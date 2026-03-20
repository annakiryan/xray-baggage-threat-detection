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

    @staticmethod
    def _letterbox(
        image: np.ndarray,
        new_shape: tuple[int, int],
        color: tuple[int, int, int] = (114, 114, 114),
    ) -> tuple[np.ndarray, float, float, float]:
        """
        Resize с сохранением пропорций + padding.

        Returns
        -------
        padded_image, scale, pad_left, pad_top
        """
        orig_h, orig_w = image.shape[:2]
        new_w, new_h = new_shape

        scale = min(new_w / orig_w, new_h / orig_h)

        resized_w = int(round(orig_w * scale))
        resized_h = int(round(orig_h * scale))

        resized = cv2.resize(
            image, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR
        )

        pad_w = new_w - resized_w
        pad_h = new_h - resized_h

        pad_left = pad_w / 2
        pad_right = pad_w - pad_left
        pad_top = pad_h / 2
        pad_bottom = pad_h - pad_top

        top = int(round(pad_top - 0.1))
        bottom = int(round(pad_bottom + 0.1))
        left = int(round(pad_left - 0.1))
        right = int(round(pad_right + 0.1))

        padded = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=color,
        )

        return padded, scale, left, top

    def preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        """
        preprocess с letterbox.

        Returns
        -------
        input_tensor, meta
        """
        if frame is None:
            raise ValueError("Получен пустой кадр для preprocess")

        input_cfg = self.model_config.input
        orig_h, orig_w = frame.shape[:2]

        image, scale, pad_left, pad_top = self._letterbox(
            frame,
            new_shape=(input_cfg.width, input_cfg.height),
        )

        if input_cfg.color_format.lower() == "rgb":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif input_cfg.color_format.lower() == "bgr":
            pass
        else:
            raise ValueError(f"Неподдерживаемый color_format: {input_cfg.color_format}")

        image = image.astype(np.float32)

        if input_cfg.normalize:
            image = image / input_cfg.scale

        mean = np.array(input_cfg.mean, dtype=np.float32).reshape(1, 1, 3)
        std = np.array(input_cfg.std, dtype=np.float32).reshape(1, 1, 3)
        image = (image - mean) / std

        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0).astype(np.float32)

        meta = {
            "orig_width": orig_w,
            "orig_height": orig_h,
            "input_width": input_cfg.width,
            "input_height": input_cfg.height,
            "scale": scale,
            "pad_left": pad_left,
            "pad_top": pad_top,
        }

        return image, meta

    def infer(self, input_tensor: np.ndarray) -> List[np.ndarray]:
        if self.session is None:
            raise RuntimeError("ONNX-сессия не инициализирована")

        return self.session.run(
            self.output_names,
            {self.input_name: input_tensor},
        )

    def predict_raw(self, frame: np.ndarray) -> tuple[List[np.ndarray], dict[str, Any]]:
        input_tensor, meta = self.preprocess(frame)
        outputs = self.infer(input_tensor)
        return outputs, meta

    def get_runtime_info(self) -> dict[str, Any]:
        if self.session is None:
            raise RuntimeError("ONNX-сессия не инициализирована")

        return {
            "device_requested": self.device,
            "available_providers": ort.get_available_providers(),
            "session_providers": self.session.get_providers(),
            "input_name": self.input_name,
            "output_names": self.output_names,
        }
