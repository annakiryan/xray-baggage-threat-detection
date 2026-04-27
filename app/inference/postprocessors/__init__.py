from abc import ABC, abstractmethod
from typing import List
from app.domain.entities import Detection


class BasePostprocessor(ABC):
    @abstractmethod
    def process(
        self,
        raw_outputs: List,
        original_width: int,
        original_height: int,
        confidence_threshold: float,
        iou_threshold: float,
        preprocess_meta: dict | None = None,
    ) -> List[Detection]:
        pass
