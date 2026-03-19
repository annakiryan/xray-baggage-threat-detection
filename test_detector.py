from pathlib import Path

import cv2

from app.services.config_service import ConfigService
from app.core.model_config import ModelConfigService
from app.core.detector import OnnxDetector
from app.core.postprocess import get_postprocessor
from app.core.drawing import draw_all


def main():
    # 1. Загружаем общий конфиг приложения
    app_config = ConfigService.load_app_config("configs/app_config.json")

    # 2. Указываем путь к конфигу модели
    model_config_path = "models/xray_yolo_nano_1/config.json"
    model_config = ModelConfigService.load_model_config(model_config_path)

    # 3. Создаём детектор
    detector = OnnxDetector(
        model_config=model_config,
        device=app_config.device,
    )

    # 4. Выводим информацию о runtime
    runtime_info = detector.get_runtime_info()
    print("=== RUNTIME INFO ===")
    print(runtime_info)
    print()

    # 5. Загружаем тестовое изображение
    image_path = Path("data/test1.png")
    if not image_path.exists():
        raise FileNotFoundError(
            f"Тестовое изображение не найдено: {image_path}\n"
            f"Положи картинку в data/test.jpg"
        )

    frame = cv2.imread(str(image_path))
    if frame is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    print(f"Image shape: {frame.shape}")

    # 6. Сырой инференс
    raw_outputs, preprocess_meta = detector.predict_raw(frame)

    print("\n=== RAW OUTPUTS ===")
    for i, out in enumerate(raw_outputs):
        print(f"Output #{i}: shape={out.shape}, dtype={out.dtype}")

    # 7. Постобработка
    postprocessor = get_postprocessor(model_config)

    detections = postprocessor.process(
        raw_outputs=raw_outputs,
        original_width=frame.shape[1],
        original_height=frame.shape[0],
        confidence_threshold=app_config.default_confidence_threshold,
        iou_threshold=app_config.default_iou_threshold,
        preprocess_meta=preprocess_meta,
    )

    result_frame = draw_all(
        frame=frame,
        detections=detections,
        model_name=model_config.model_name,
        fps=30.0,  # можно временно для теста
        inference_time_ms=50.0,  # или вычислять
        device=app_config.device,
    )

    cv2.imshow("Result", result_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imwrite("data/result.jpg", result_frame)

    # 8. Вывод детекций
    print("\n=== DETECTIONS ===")
    if not detections:
        print("Объекты не найдены")
    else:
        for idx, det in enumerate(detections, start=1):
            print(
                f"{idx}. class_id={det.class_id}, "
                f"class_name={det.class_name}, "
                f"confidence={det.confidence:.4f}, "
                f"bbox={det.bbox}"
            )


if __name__ == "__main__":
    main()
