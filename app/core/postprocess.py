from app.core.postprocessors.detr import DetrPostprocessor
from app.core.postprocessors.yolo import YoloPostprocessor
from app.domain.entities import ModelConfig


POSTPROCESSOR_REGISTRY = {
    "yolo": YoloPostprocessor,
    "detr": DetrPostprocessor,
}


def get_postprocessor(model_config: ModelConfig):
    output_format = model_config.output.format.lower()

    postprocessor_cls = POSTPROCESSOR_REGISTRY.get(output_format)
    if postprocessor_cls is None:
        raise ValueError(
            f"Неподдерживаемый формат выхода модели: {model_config.output.format}"
        )

    return postprocessor_cls(model_config)
