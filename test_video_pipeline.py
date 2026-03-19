import time
from pathlib import Path

import cv2

from app.services.config_service import ConfigService
from app.core.model_config import ModelConfigService
from app.core.detector import OnnxDetector
from app.core.postprocess import get_postprocessor
from app.core.video_source import VideoSource
from app.core.drawing import draw_all


VIDEO_PATH = "data/videos/test.mp4"
MODEL_CONFIG_PATH = "models/xray_yolo_nano_1/config.json"


def main():
    app_config = ConfigService.load_app_config("configs/app_config.json")
    model_config = ModelConfigService.load_model_config(MODEL_CONFIG_PATH)

    detector = OnnxDetector(
        model_config=model_config,
        device=app_config.device,
    )
    postprocessor = get_postprocessor(model_config)

    video_source = VideoSource(VIDEO_PATH)
    video_source.open()

    print("=== VIDEO SOURCE INFO ===")
    print(video_source.get_source_info())
    print()
    print("Нажми 'q' для выхода")

    frame_index = 0
    process_every_n = app_config.default_frame_skip

    total_start_time = time.perf_counter()
    last_detections = []
    last_inference_time_ms = 0.0

    try:
        while True:
            ok, frame = video_source.read()
            if not ok or frame is None:
                print("Видео завершено")
                break

            frame_index += 1

            # По умолчанию показываем последние детекции
            detections_to_draw = last_detections
            inference_time_ms = last_inference_time_ms

            if frame_index % process_every_n == 0:
                start_infer = time.perf_counter()

                raw_outputs, preprocess_meta = detector.predict_raw(frame)

                current_detections = postprocessor.process(
                    raw_outputs=raw_outputs,
                    original_width=frame.shape[1],
                    original_height=frame.shape[0],
                    confidence_threshold=app_config.default_confidence_threshold,
                    iou_threshold=app_config.default_iou_threshold,
                    preprocess_meta=preprocess_meta,
                )

                inference_time_ms = (time.perf_counter() - start_infer) * 1000.0

                # Обновляем последние детекции только если инференс отработал
                last_detections = current_detections
                last_inference_time_ms = inference_time_ms
                detections_to_draw = current_detections

            elapsed_total = time.perf_counter() - total_start_time
            pipeline_fps = frame_index / elapsed_total if elapsed_total > 0 else 0.0

            result_frame = draw_all(
                frame=frame,
                detections=detections_to_draw,
                model_name=model_config.model_name,
                fps=pipeline_fps,
                inference_time_ms=inference_time_ms,
                device=app_config.device,
            )

            cv2.imshow("XRay Video Pipeline", result_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Остановка по клавише 'q'")
                break

    finally:
        video_source.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
