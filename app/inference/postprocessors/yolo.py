from typing import List

import cv2
import numpy as np

from app.inference.postprocessors import BasePostprocessor
from app.domain.entities import Detection, ModelConfig


class YoloPostprocessor(BasePostprocessor):
    """
    Постобработка YOLO-подобного выхода ONNX-модели.
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
        preprocess_meta: dict | None = None,
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
            preprocess_meta=preprocess_meta,
        )

        detections = self._apply_nms(detections, iou_threshold)
        max_detections = self.model_config.postprocess.max_detections
        return detections[:max_detections]

    @staticmethod
    def _prepare_predictions(predictions: np.ndarray) -> np.ndarray:
        if predictions.ndim == 3:
            predictions = predictions[0]

        if predictions.ndim != 2:
            raise ValueError(
                f"Ожидался выход модели размерности 2 или 3, получено: shape={predictions.shape}"
            )

        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        return predictions

    def _decode_predictions(
        self,
        predictions: np.ndarray,
        original_width: int,
        original_height: int,
        confidence_threshold: float,
        preprocess_meta: dict | None,
    ) -> List[Detection]:
        detections: List[Detection] = []

        class_names = self.model_config.classes
        num_classes = len(class_names)

        for pred in predictions:
            values_count = pred.shape[0]

            if values_count == 4 + num_classes:
                cx, cy, w, h = pred[:4]
                class_scores = pred[4:]
                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])

            elif values_count == 5 + num_classes:
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

            x1, y1, x2, y2 = self._xywh_to_xyxy_letterbox(
                cx=float(cx),
                cy=float(cy),
                w=float(w),
                h=float(h),
                original_width=original_width,
                original_height=original_height,
                preprocess_meta=preprocess_meta,
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
    def _xywh_to_xyxy_letterbox(
        cx: float,
        cy: float,
        w: float,
        h: float,
        original_width: int,
        original_height: int,
        preprocess_meta: dict | None,
    ) -> tuple[int, int, int, int]:
        """
        Перевод bbox из координат letterbox-входа обратно в координаты исходного изображения.
        """
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0

        if preprocess_meta is not None:
            scale = preprocess_meta["scale"]
            pad_left = preprocess_meta["pad_left"]
            pad_top = preprocess_meta["pad_top"]

            x1 = (x1 - pad_left) / scale
            y1 = (y1 - pad_top) / scale
            x2 = (x2 - pad_left) / scale
            y2 = (y2 - pad_top) / scale

        x1 = int(max(0, min(round(x1), original_width - 1)))
        y1 = int(max(0, min(round(y1), original_height - 1)))
        x2 = int(max(0, min(round(x2), original_width - 1)))
        y2 = int(max(0, min(round(y2), original_height - 1)))

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
