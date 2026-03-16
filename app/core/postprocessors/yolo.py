from typing import List

import cv2
import numpy as np

from app.core.postprocessors import BasePostprocessor
from app.domain.entities import Detection, ModelConfig


class YoloPostprocessor(BasePostprocessor):
    """
    Постобработка YOLO-подобного выхода ONNX-модели.

    Поддерживаемые форматы одного предсказания:
    1) [cx, cy, w, h, class_scores...]
    2) [cx, cy, w, h, objectness, class_scores...]

    Типичный выход модели:
    - (1, C, N)
    - (C, N)
    - (N, C)

    На выходе:
    - List[Detection]
    """

    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config

    def process(
        self,
        raw_outputs: list,
        original_width: int,
        original_height: int,
        confidence_threshold: float,
        iou_threshold: float,
    ) -> List[Detection]:
        if not raw_outputs:
            return []

        predictions = raw_outputs[0]
        predictions = self._prepare_predictions(predictions)

        detections = self._decode_predictions(
            predictions=predictions,
            original_width=original_width,
            original_height=original_height,
            confidence_threshold=confidence_threshold,
        )

        detections = self._apply_nms(detections, iou_threshold)

        max_detections = self.model_config.postprocess.max_detections
        return detections[:max_detections]

    @staticmethod
    def _prepare_predictions(predictions: np.ndarray) -> np.ndarray:
        """
        Приводит выход модели к форме (N, C),
        где:
        - N: число предсказаний
        - C: число параметров одного предсказания
        """
        if predictions.ndim == 3:
            # Например: (1, C, N) -> (C, N)
            predictions = predictions[0]

        if predictions.ndim != 2:
            raise ValueError(
                f"Ожидался выход модели размерности 2 или 3, получено: shape={predictions.shape}"
            )

        # Частый случай YOLO ONNX: (C, N) -> (N, C)
        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        return predictions

    def _decode_predictions(
        self,
        predictions: np.ndarray,
        original_width: int,
        original_height: int,
        confidence_threshold: float,
    ) -> List[Detection]:
        detections: List[Detection] = []

        input_w = self.model_config.input.width
        input_h = self.model_config.input.height
        class_names = self.model_config.classes
        num_classes = len(class_names)

        for pred in predictions:
            values_count = pred.shape[0]

            if values_count == 4 + num_classes:
                # [cx, cy, w, h, class_scores...]
                cx, cy, w, h = pred[:4]
                class_scores = pred[4:]

                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])

            elif values_count == 5 + num_classes:
                # [cx, cy, w, h, objectness, class_scores...]
                cx, cy, w, h = pred[:4]
                objectness = float(pred[4])
                class_scores = pred[5:]

                class_id = int(np.argmax(class_scores))
                confidence = float(objectness * class_scores[class_id])

            else:
                raise ValueError(
                    f"Неожиданное число параметров в предсказании: {values_count}. "
                    f"Ожидалось {4 + num_classes} или {5 + num_classes}."
                )

            if confidence < confidence_threshold:
                continue

            x1, y1, x2, y2 = self._xywh_to_xyxy(
                cx=float(cx),
                cy=float(cy),
                w=float(w),
                h=float(h),
                input_w=input_w,
                input_h=input_h,
                original_width=original_width,
                original_height=original_height,
            )

            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_names[class_id],
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                )
            )

        return detections

    @staticmethod
    def _xywh_to_xyxy(
        cx: float,
        cy: float,
        w: float,
        h: float,
        input_w: int,
        input_h: int,
        original_width: int,
        original_height: int,
    ) -> tuple[int, int, int, int]:
        """
        Переводит bbox из [cx, cy, w, h] в [x1, y1, x2, y2]
        и масштабирует из размеров входа модели в размеры исходного кадра.
        """
        x1 = (cx - w / 2.0) * original_width / input_w
        y1 = (cy - h / 2.0) * original_height / input_h
        x2 = (cx + w / 2.0) * original_width / input_w
        y2 = (cy + h / 2.0) * original_height / input_h

        x1 = int(max(0, min(x1, original_width - 1)))
        y1 = int(max(0, min(y1, original_height - 1)))
        x2 = int(max(0, min(x2, original_width - 1)))
        y2 = int(max(0, min(y2, original_height - 1)))

        return x1, y1, x2, y2

    @staticmethod
    def _apply_nms(
        detections: List[Detection],
        iou_threshold: float,
    ) -> List[Detection]:
        if not detections:
            return []

        boxes = []
        scores = []

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            width = max(0, x2 - x1)
            height = max(0, y2 - y1)

            boxes.append([x1, y1, width, height])
            scores.append(float(det.confidence))

        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes,
            scores=scores,
            score_threshold=0.0,
            nms_threshold=iou_threshold,
        )

        if len(indices) == 0:
            return []

        flat_indices = np.array(indices).flatten().tolist()
        return [detections[i] for i in flat_indices]
