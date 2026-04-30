import json
from pathlib import Path

from app.domain.entities import DetectionEvent, SessionSummary
from app.session.session_results_service import SessionResultsService


def test_create_session_structure_creates_required_directories(tmp_path):
    video_path = tmp_path / "video.mp4"

    session = SessionResultsService.create_session_structure(
        results_dir=tmp_path,
        video_path=video_path,
    )

    assert session.session_dir.exists()
    assert session.session_dir.is_dir()

    assert session.detections_dir.exists()
    assert session.detections_dir.is_dir()

    assert session.manual_captures_dir.exists()
    assert session.manual_captures_dir.is_dir()

    assert session.summary_path.exists()
    assert session.summary_path.is_file()


def test_create_session_structure_initializes_summary(tmp_path):
    video_path = tmp_path / "video.mp4"

    session = SessionResultsService.create_session_structure(
        results_dir=tmp_path,
        video_path=video_path,
    )

    assert session.summary.session_id.startswith("session_")
    assert session.summary.video_path == str(video_path)
    assert session.summary.started_at
    assert session.summary.finished_at is None
    assert session.summary.total_detection_events == 0
    assert session.summary.class_counts == {}
    assert session.summary.events == []


def test_create_session_structure_writes_summary_to_json(tmp_path):
    video_path = tmp_path / "video.mp4"

    session = SessionResultsService.create_session_structure(
        results_dir=tmp_path,
        video_path=video_path,
    )

    with session.summary_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["session_id"] == session.summary.session_id
    assert data["video_path"] == str(video_path)
    assert data["started_at"] == session.summary.started_at
    assert data["finished_at"] is None
    assert data["total_detection_events"] == 0
    assert data["class_counts"] == {}
    assert data["events"] == []


def test_save_summary_creates_parent_directory_and_writes_json(tmp_path):
    summary_path = tmp_path / "nested" / "session_summary.json"

    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    SessionResultsService.save_summary(summary, summary_path)

    assert summary_path.exists()

    with summary_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["session_id"] == "session_test"
    assert data["video_path"] == "video.mp4"
    assert data["started_at"] == "2026-04-30 10:00:00"


def test_append_detection_event_updates_summary_object(tmp_path):
    summary_path = tmp_path / "session_summary.json"

    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    event = DetectionEvent(
        event_id=1,
        class_ids=[0, 1],
        class_names=["gun", "knife"],
        frame_index=25,
        timestamp_sec=1.0,
        image_path="detections/capture.jpg",
        bboxes=[(10, 10, 100, 100), (120, 120, 200, 200)],
    )

    SessionResultsService.append_detection_event(
        summary=summary,
        summary_path=summary_path,
        event=event,
    )

    assert summary.total_detection_events == 1
    assert summary.events == [event]
    assert summary.class_counts == {
        "gun": 1,
        "knife": 1,
    }


def test_append_detection_event_writes_updated_summary_to_json(tmp_path):
    summary_path = tmp_path / "session_summary.json"

    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    event = DetectionEvent(
        event_id=1,
        class_ids=[0],
        class_names=["gun"],
        frame_index=10,
        timestamp_sec=0.4,
        image_path="detections/capture.jpg",
        bboxes=[(1, 2, 3, 4)],
    )

    SessionResultsService.append_detection_event(
        summary=summary,
        summary_path=summary_path,
        event=event,
    )

    with summary_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["total_detection_events"] == 1
    assert data["class_counts"] == {"gun": 1}
    assert data["events"][0]["event_id"] == 1
    assert data["events"][0]["class_names"] == ["gun"]
    assert data["events"][0]["frame_index"] == 10
    assert data["events"][0]["timestamp_sec"] == 0.4
    assert data["events"][0]["image_path"] == "detections/capture.jpg"


def test_append_detection_event_accumulates_class_counts(tmp_path):
    summary_path = tmp_path / "session_summary.json"

    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    first_event = DetectionEvent(
        event_id=1,
        class_ids=[0],
        class_names=["gun"],
        frame_index=10,
        timestamp_sec=0.4,
        image_path="detections/1.jpg",
    )

    second_event = DetectionEvent(
        event_id=2,
        class_ids=[0, 1],
        class_names=["gun", "knife"],
        frame_index=20,
        timestamp_sec=0.8,
        image_path="detections/2.jpg",
    )

    SessionResultsService.append_detection_event(summary, summary_path, first_event)
    SessionResultsService.append_detection_event(summary, summary_path, second_event)

    assert summary.total_detection_events == 2
    assert summary.class_counts == {
        "gun": 2,
        "knife": 1,
    }


def test_finalize_summary_sets_finished_at_and_writes_json(tmp_path):
    summary_path = tmp_path / "session_summary.json"

    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    SessionResultsService.finalize_summary(summary, summary_path)

    assert summary.finished_at is not None

    with summary_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["finished_at"] == summary.finished_at


def test_save_detection_frame_uses_capture_service(monkeypatch, tmp_path):
    calls = {}

    def fake_save_frame_with_overlay(frame, results_dir, file_prefix):
        calls["frame"] = frame
        calls["results_dir"] = results_dir
        calls["file_prefix"] = file_prefix
        return Path(results_dir) / "saved.jpg"

    monkeypatch.setattr(
        "app.session.session_results_service.CaptureService.save_frame_with_overlay",
        fake_save_frame_with_overlay,
    )

    frame = object()
    detections_dir = tmp_path / "detections"

    result = SessionResultsService.save_detection_frame(
        frame=frame,
        detections_dir=detections_dir,
        event_id=1,
    )

    assert result == str(detections_dir / "saved.jpg")
    assert calls["frame"] is frame
    assert calls["results_dir"] == str(detections_dir)
    assert calls["file_prefix"] == ""
