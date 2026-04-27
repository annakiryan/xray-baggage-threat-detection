from typing import List

from app.inference.postprocessors import BasePostprocessor
from app.domain.entities import Detection, ModelConfig


class DetrPostprocessor(BasePostprocessor):
    """
    Каркас постпроцессора для DETR-подобных моделей.

    ВАЖНО:
    Реальная реализация зависит от конкретного формата выхода модели.
    У разных экспортов DETR могут различаться:
    - имена выходов,
    - наличие logits / scores / boxes,
    - формат координат,
    - необходимость сигмоиды / softmax.

    Поэтому здесь пока оставлен явный NotImplementedError.
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
        raise NotImplementedError(
            "DETR postprocessing пока не реализован. "
            "Нужно смотреть конкретный формат выхода ONNX-модели."
        )
