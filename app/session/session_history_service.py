from dataclasses import dataclass
from json import JSONDecodeError
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistorySessionData:
    session_dir: Path
    summary_path: Path | None
    title: str
    class_counts: dict[str, int]
    detection_images: list[Path]
    manual_images: list[Path]


class SessionHistoryService:
    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    @staticmethod
    def load_sessions(results_dir: str | Path) -> list[HistorySessionData]:
        results_path = Path(results_dir)
        if not results_path.exists():
            return []

        sessions: list[HistorySessionData] = []

        for session_dir in sorted(results_path.iterdir(), reverse=True):
            if not session_dir.is_dir():
                continue

            summary_path = session_dir / "session_summary.json"
            summary = SessionHistoryService.read_summary(summary_path)

            detections_dir = session_dir / "detections"
            manual_captures_dir = session_dir / "manual_captures"

            sessions.append(
                HistorySessionData(
                    session_dir=session_dir,
                    summary_path=summary_path if summary_path.exists() else None,
                    title=SessionHistoryService.make_session_title(session_dir, summary),
                    class_counts=summary.get("class_counts", {}),
                    detection_images=SessionHistoryService.collect_detection_images(
                        summary=summary,
                        detections_dir=detections_dir,
                    ),
                    manual_images=SessionHistoryService.load_images_from_dir(
                        manual_captures_dir
                    ),
                )
            )

        return sessions

    @staticmethod
    def read_summary(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, JSONDecodeError):
            return {}

    @staticmethod
    def make_session_title(session_dir: Path, summary: dict[str, Any]) -> str:
        started_at = summary.get("started_at")
        if started_at:
            return started_at.replace("-", ".")[:16]

        return session_dir.name.replace("session_", "").replace("_", " ")

    @staticmethod
    def collect_detection_images(
        summary: dict[str, Any],
        detections_dir: Path,
    ) -> list[Path]:
        images: list[Path] = []
        session_root = detections_dir.parent.resolve()

        for event in summary.get("events", []):
            image_path = event.get("image_path")
            if not image_path:
                continue

            path = Path(image_path)
            try:
                resolved = path.resolve()
            except OSError:
                continue

            if not resolved.exists() or not resolved.is_file():
                continue

            if session_root == resolved or session_root in resolved.parents:
                images.append(resolved)

        if images:
            return images

        return SessionHistoryService.load_images_from_dir(detections_dir)

    @staticmethod
    def load_images_from_dir(directory: str | Path | None) -> list[Path]:
        if not directory:
            return []

        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return []

        images = [
            item
            for item in path.iterdir()
            if item.is_file()
            and item.suffix.lower() in SessionHistoryService.IMAGE_SUFFIXES
        ]
        images.sort(key=lambda p: p.name.lower())
        return images
