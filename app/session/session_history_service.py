from dataclasses import dataclass
from json import JSONDecodeError
import json
from pathlib import Path
from typing import Any
import shutil


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
                    title=SessionHistoryService.make_session_title(
                        session_dir, summary
                    ),
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
    
    @staticmethod
    def delete_sessions(session_dirs: list[Path]) -> None:
        for session_dir in session_dirs:
            path = Path(session_dir)

            if path.exists() and path.is_dir():
                shutil.rmtree(path)

    @staticmethod
    def delete_images_from_session(
        session: HistorySessionData,
        image_paths: list[Path],
    ) -> None:
        resolved_deleted = set()

        for image_path in image_paths:
            path = Path(image_path)

            try:
                resolved = path.resolve()
            except OSError:
                continue

            if resolved.exists() and resolved.is_file():
                resolved.unlink()
                resolved_deleted.add(resolved)

        if session.summary_path is None or not session.summary_path.exists():
            return

        summary = SessionHistoryService.read_summary(session.summary_path)
        events = summary.get("events", [])

        if not isinstance(events, list):
            return

        updated_events = []

        for event in events:
            image_path = event.get("image_path")

            if not image_path:
                updated_events.append(event)
                continue

            try:
                resolved_event_path = Path(image_path).resolve()
            except OSError:
                updated_events.append(event)
                continue

            if resolved_event_path not in resolved_deleted:
                updated_events.append(event)

        summary["events"] = updated_events
        summary["total_detection_events"] = len(updated_events)
        summary["class_counts"] = SessionHistoryService._make_class_counts(
            updated_events
        )

        with session.summary_path.open("w", encoding="utf-8") as file:
            json.dump(
                summary,
                file,
                ensure_ascii=False,
                indent=2,
            )

    @staticmethod
    def _make_class_counts(events: list[dict[str, Any]]) -> dict[str, int]:
        class_counts: dict[str, int] = {}

        for event in events:
            class_names = event.get("class_names", [])

            if not isinstance(class_names, list):
                continue

            for class_name in class_names:
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

        return class_counts
