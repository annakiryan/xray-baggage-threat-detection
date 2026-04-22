from json import JSONDecodeError
import json
from pathlib import Path
from typing import Any


class SessionHistoryService:
    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    @staticmethod
    def load_sessions(results_dir: str | Path) -> list[dict[str, Any]]:
        results_path = Path(results_dir)
        if not results_path.exists():
            return []

        sessions: list[dict[str, Any]] = []

        for session_dir in results_path.iterdir():
            if not session_dir.is_dir():
                continue

            summary_path = session_dir / "session_summary.json"
            if not summary_path.exists():
                continue

            try:
                with summary_path.open("r", encoding="utf-8") as f:
                    summary = json.load(f)
            except (OSError, JSONDecodeError):
                continue

            detections_dir = session_dir / "detections"
            manual_captures_dir = session_dir / "manual_captures"

            sessions.append(
                {
                    "session_id": summary.get("session_id", session_dir.name),
                    "session_dir": session_dir,
                    "summary_path": summary_path,
                    "summary": summary,
                    "detections_dir": detections_dir,
                    "manual_captures_dir": manual_captures_dir,
                    "video_path": summary.get("video_path", ""),
                    "started_at": summary.get("started_at", ""),
                    "finished_at": summary.get("finished_at", ""),
                    "total_detection_events": summary.get("total_detection_events", 0),
                    "class_counts": summary.get("class_counts", {}),
                    "events": summary.get("events", []),
                }
            )

        sessions.sort(key=lambda item: item.get("started_at", ""), reverse=True)
        return sessions

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
            if item.is_file() and item.suffix.lower() in SessionHistoryService.IMAGE_SUFFIXES
        ]
        images.sort(key=lambda p: p.name.lower())
        return images

    @staticmethod
    def _normalize_query(query: str) -> str:
        return query.strip().lower()

    @staticmethod
    def matches_session(session: dict[str, Any], query: str) -> bool:
        text = SessionHistoryService._normalize_query(query)
        if not text:
            return True

        haystacks: list[str] = [
            str(session.get("session_id", "")),
            str(session.get("started_at", "")),
            str(session.get("finished_at", "")),
            str(session.get("video_path", "")),
        ]

        class_counts = session.get("class_counts", {})
        haystacks.extend(class_counts.keys())

        for image_path in session.get("auto_images", []):
            haystacks.append(image_path.name)

        for image_path in session.get("manual_images", []):
            haystacks.append(image_path.name)

        full_text = " ".join(haystacks).lower()
        return text in full_text

    @staticmethod
    def filter_sessions(sessions: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        text = SessionHistoryService._normalize_query(query)
        if not text:
            return sessions

        return [
            session
            for session in sessions
            if SessionHistoryService.matches_session(session, text)
        ]

    @staticmethod
    def filter_session_content(
        session: dict[str, Any],
        query: str,
    ) -> dict[str, Any]:
        text = SessionHistoryService._normalize_query(query)
        if not text:
            return {
                "show_statistics": True,
                "auto_images": session.get("auto_images", []),
                "manual_images": session.get("manual_images", []),
            }

        stats_tokens = [
            str(session.get("session_id", "")),
            str(session.get("started_at", "")),
            str(session.get("finished_at", "")),
            str(session.get("video_path", "")),
            "статистика",
        ]
        stats_tokens.extend(session.get("class_counts", {}).keys())
        stats_text = " ".join(stats_tokens).lower()

        filtered_auto = [
            path
            for path in session.get("auto_images", [])
            if text in path.name.lower() or text in "автоматические снимки"
        ]
        filtered_manual = [
            path
            for path in session.get("manual_images", [])
            if text in path.name.lower() or text in "ручные снимки"
        ]

        show_statistics = text in stats_text

        if filtered_auto or filtered_manual:
            return {
                "show_statistics": show_statistics,
                "auto_images": filtered_auto,
                "manual_images": filtered_manual,
            }

        return {
            "show_statistics": show_statistics,
            "auto_images": filtered_auto,
            "manual_images": filtered_manual,
        }