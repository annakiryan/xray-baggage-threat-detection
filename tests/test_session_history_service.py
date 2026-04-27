import json
import tempfile
import unittest
from pathlib import Path

from app.session.session_history_service import SessionHistoryService


class SessionHistoryServiceTests(unittest.TestCase):
    def test_load_sessions_reads_summary_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            session_dir = root / "session_2026-01-01_10-00-00"
            detections_dir = session_dir / "detections"
            manual_dir = session_dir / "manual_captures"
            detections_dir.mkdir(parents=True)
            manual_dir.mkdir(parents=True)

            event_image = detections_dir / "event_1.png"
            event_image.write_bytes(b"png")
            (manual_dir / "manual_1.jpg").write_bytes(b"jpg")

            summary = {
                "started_at": "2026-01-01 10:00:00",
                "class_counts": {"knife": 2},
                "events": [{"image_path": str(event_image)}],
            }
            (session_dir / "session_summary.json").write_text(
                json.dumps(summary, ensure_ascii=False),
                encoding="utf-8",
            )

            sessions = SessionHistoryService.load_sessions(root)

            self.assertEqual(len(sessions), 1)
            loaded = sessions[0]
            self.assertEqual(loaded.title, "2026.01.01 10:00")
            self.assertEqual(loaded.class_counts, {"knife": 2})
            self.assertEqual(loaded.detection_images, [event_image])
            self.assertEqual(loaded.manual_images, [manual_dir / "manual_1.jpg"])

    def test_load_sessions_falls_back_to_detections_dir_when_no_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            session_dir = root / "session_2026-01-01_11-00-00"
            detections_dir = session_dir / "detections"
            session_dir.mkdir(parents=True)
            detections_dir.mkdir(parents=True)

            fallback_image = detections_dir / "frame_10.webp"
            fallback_image.write_bytes(b"webp")

            summary = {
                "started_at": "2026-01-01 11:00:00",
                "class_counts": {},
                "events": [],
            }
            (session_dir / "session_summary.json").write_text(
                json.dumps(summary, ensure_ascii=False),
                encoding="utf-8",
            )

            sessions = SessionHistoryService.load_sessions(root)

            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].detection_images, [fallback_image])


if __name__ == "__main__":
    unittest.main()
