from pathlib import Path

import cv2
from ultralytics import YOLO

from app.core.detector import OnnxDetector
from app.core.model_config import ModelConfigService
from app.core.postprocess import get_postprocessor
from app.core.drawing import draw_all


PT_MODEL_PATH = "best.pt"
ONNX_CONFIG_PATH = "models/xray_yolo_nano_1/config.json"
IMAGE_PATH = "data/pidray_xray_hard03619.png"
OUTPUT_DIR = "data/compare_results"

# ВАЖНО:
# здесь порядок должен совпадать с порядком классов в твоем датасете / config.json
CLASS_NAMES = [
    "Дубинка",
    "Плоскогубцы",
    "Молоток",
    "Пауэрбанк",
    "Ножницы",
    "Гаечный ключ",
    "Пистолет",
    "Пуля",
    "Спрей",
    "Наручники",
    "Нож",
    "Зажигалка",
]


def run_pt_inference(image_path: str):
    model = YOLO(PT_MODEL_PATH)
    results = model(image_path, verbose=False)

    result = results[0]
    detections = []

    if result.boxes is not None:
        boxes = result.boxes
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy().astype(int)

        for bbox, conf, class_id in zip(xyxy, confs, class_ids):
            x1, y1, x2, y2 = map(int, bbox)
            class_name = (
                CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else str(class_id)
            )

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": float(conf),
                    "bbox": (x1, y1, x2, y2),
                }
            )

    return detections


def run_onnx_inference(image_path: str):
    model_config = ModelConfigService.load_model_config(ONNX_CONFIG_PATH)
    detector = OnnxDetector(model_config=model_config, device="cpu")
    postprocessor = get_postprocessor(model_config)

    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    raw_outputs, preprocess_meta = detector.predict_raw(frame)

    detections = postprocessor.process(
        raw_outputs=raw_outputs,
        original_width=frame.shape[1],
        original_height=frame.shape[0],
        confidence_threshold=0.01,
        iou_threshold=0.5,
        preprocess_meta=preprocess_meta,
    )

    return detections


def print_pt_detections(detections):
    print("\n=== PT DETECTIONS ===")
    if not detections:
        print("Ничего не найдено")
        return

    for i, det in enumerate(detections, start=1):
        print(
            f"{i}. class_id={det['class_id']}, "
            f"class_name={det['class_name']}, "
            f"confidence={det['confidence']:.4f}, "
            f"bbox={det['bbox']}"
        )


def print_onnx_detections(detections):
    print("\n=== ONNX DETECTIONS ===")
    if not detections:
        print("Ничего не найдено")
        return

    for i, det in enumerate(detections, start=1):
        print(
            f"{i}. class_id={det.class_id}, "
            f"class_name={det.class_name}, "
            f"confidence={det.confidence:.4f}, "
            f"bbox={det.bbox}"
        )


def save_visualizations(image_path: str, pt_detections, onnx_detections):
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    # Для pt преобразуем к формату, который понимает draw_all
    from app.domain.entities import Detection

    pt_det_objects = [
        Detection(
            class_id=det["class_id"],
            class_name=det["class_name"],
            confidence=det["confidence"],
            bbox=det["bbox"],
        )
        for det in pt_detections
    ]

    pt_frame = draw_all(
        frame=frame,
        detections=pt_det_objects,
        model_name="PT model",
        fps=None,
        inference_time_ms=None,
        device="cpu",
    )

    onnx_frame = draw_all(
        frame=frame,
        detections=onnx_detections,
        model_name="ONNX model",
        fps=None,
        inference_time_ms=None,
        device="cpu",
    )

    pt_path = output_dir / "pt_result.jpg"
    onnx_path = output_dir / "onnx_result.jpg"

    cv2.imwrite(str(pt_path), pt_frame)
    cv2.imwrite(str(onnx_path), onnx_frame)

    print(f"\nСохранено:")
    print(f"PT:   {pt_path}")
    print(f"ONNX: {onnx_path}")


def main():
    if not Path(PT_MODEL_PATH).exists():
        raise FileNotFoundError(f".pt модель не найдена: {PT_MODEL_PATH}")

    if not Path(ONNX_CONFIG_PATH).exists():
        raise FileNotFoundError(f"config.json не найден: {ONNX_CONFIG_PATH}")

    if not Path(IMAGE_PATH).exists():
        raise FileNotFoundError(f"Изображение не найдено: {IMAGE_PATH}")

    pt_detections = run_pt_inference(IMAGE_PATH)
    onnx_detections = run_onnx_inference(IMAGE_PATH)

    print_pt_detections(pt_detections)
    print_onnx_detections(onnx_detections)

    save_visualizations(IMAGE_PATH, pt_detections, onnx_detections)


if __name__ == "__main__":
    main()
