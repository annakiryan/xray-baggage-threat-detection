import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import cv2

from app.domain.entities import DetectionEvent, SessionSummary
from app.video.capture_service import CaptureService


class SessionResultsService:
    @staticmethod
    def create_session_structure(
        results_dir: str, video_path: str
    ) -> dict[str, Path | SessionSummary]:
        base_results_dir = Path(results_dir)
        base_results_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        session_id = now.strftime("session_%Y-%m-%d_%H-%M-%S")

        session_dir = base_results_dir / session_id
        detections_dir = session_dir / "detections"
        manual_captures_dir = session_dir / "manual_captures"
        summary_path = session_dir / "session_summary.json"

        session_dir.mkdir(parents=True, exist_ok=True)
        detections_dir.mkdir(parents=True, exist_ok=True)
        manual_captures_dir.mkdir(parents=True, exist_ok=True)

        summary = SessionSummary(
            session_id=session_id,
            video_path=video_path,
            started_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        )

        SessionResultsService.save_summary(summary, summary_path)

        return {
            "session_dir": session_dir,
            "detections_dir": detections_dir,
            "manual_captures_dir": manual_captures_dir,
            "summary_path": summary_path,
            "summary": summary,
        }

    @staticmethod
    def save_summary(summary: SessionSummary, summary_path: str | Path) -> None:
        path = Path(summary_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                asdict(summary),
                f,
                ensure_ascii=False,
                indent=2,
            )

    @staticmethod
    def finalize_summary(summary: SessionSummary, summary_path: str | Path) -> None:
        summary.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SessionResultsService.save_summary(summary, summary_path)

    @staticmethod
    def append_detection_event(
        summary: SessionSummary,
        summary_path: str | Path,
        event: DetectionEvent,
    ) -> None:
        summary.events.append(event)
        summary.total_detection_events += 1

        for class_name in event.class_names:
            summary.class_counts[class_name] = (
                summary.class_counts.get(class_name, 0) + 1
            )

        SessionResultsService.save_summary(summary, summary_path)

    @staticmethod
    def save_detection_frame(
        frame,
        detections_dir: str | Path,
        event_id: int,
    ) -> str:
        save_path = CaptureService.save_frame_with_overlay(
            frame=frame,
            results_dir=str(detections_dir),
            file_prefix="",
        )
        return str(save_path)
