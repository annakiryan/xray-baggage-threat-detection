import json
from pathlib import Path

import numpy as np

from app.domain.entities import Detection, FrameResult, SessionSummary
from app.processing.detection_event_manager import DetectionEventManager
from app.session.session_results_service import SessionResultsService


def make_frame_result(
    detections: list[Detection],
    frame_index: int = 1,
    timestamp_sec: float = 0.04,
    width: int = 100,
    height: int = 80,
) -> FrameResult:
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    return FrameResult(
        frame=frame,
        detections=detections,
        frame_index=frame_index,
        timestamp_sec=timestamp_sec,
    )


def make_detection(
    class_id: int = 0,
    class_name: str = "gun",
    confidence: float = 0.9,
    bbox: tuple[int, int, int, int] = (10, 10, 40, 40),
) -> Detection:
    return Detection(
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
        bbox=bbox,
    )


def make_manager(tmp_path) -> tuple[DetectionEventManager, SessionSummary, Path]:
    summary = SessionSummary(
        session_id="session_test",
        video_path="video.mp4",
        started_at="2026-04-30 10:00:00",
    )

    summary_path = tmp_path / "session_summary.json"
    detections_dir = tmp_path / "detections"
    detections_dir.mkdir()

    manager = DetectionEventManager(
        session_summary=summary,
        summary_path=summary_path,
        detections_dir=detections_dir,
        event_iou_threshold=0.3,
        event_ttl_frames=15,
        right_edge_margin_px=8,
    )

    return manager, summary, summary_path


def patch_save_detection_frame(monkeypatch):
    def fake_save_detection_frame(frame, detections_dir, event_id):
        return str(Path(detections_dir) / f"detection_{event_id}.jpg")

    monkeypatch.setattr(
        SessionResultsService,
        "save_detection_frame",
        staticmethod(fake_save_detection_frame),
    )


def test_process_frame_result_does_not_create_event_without_detections(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, summary_path = make_manager(tmp_path)

    result = make_frame_result(detections=[])

    manager.process_frame_result(result)

    assert summary.total_detection_events == 0
    assert summary.events == []
    assert summary.class_counts == {}
    assert not summary_path.exists()


def test_process_frame_result_creates_event_for_new_visible_detection(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, summary_path = make_manager(tmp_path)

    detection = make_detection()
    result = make_frame_result(detections=[detection], frame_index=1)

    manager.process_frame_result(result)

    assert summary.total_detection_events == 1
    assert summary.class_counts == {"gun": 1}

    event = summary.events[0]
    assert event.event_id == 1
    assert event.class_ids == [0]
    assert event.class_names == ["gun"]
    assert event.frame_index == 1
    assert event.timestamp_sec == 0.04
    assert event.bboxes == [(10, 10, 40, 40)]
    assert event.image_path.endswith("detection_1.jpg")

    assert summary_path.exists()


def test_process_frame_result_writes_event_to_summary_json(tmp_path, monkeypatch):
    patch_save_detection_frame(monkeypatch)
    manager, summary, summary_path = make_manager(tmp_path)

    detection = make_detection()
    result = make_frame_result(detections=[detection], frame_index=3)

    manager.process_frame_result(result)

    with summary_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["total_detection_events"] == 1
    assert data["class_counts"] == {"gun": 1}
    assert data["events"][0]["event_id"] == 1
    assert data["events"][0]["class_names"] == ["gun"]
    assert data["events"][0]["frame_index"] == 3


def test_process_frame_result_does_not_save_detection_near_right_edge(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, summary_path = make_manager(tmp_path)

    detection = make_detection(
        bbox=(70, 10, 98, 40),
    )
    result = make_frame_result(detections=[detection], width=100)

    manager.process_frame_result(result)

    assert summary.total_detection_events == 0
    assert summary.events == []
    assert not summary_path.exists()


def test_process_frame_result_does_not_duplicate_same_detection_on_next_frame(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, _ = make_manager(tmp_path)

    first_result = make_frame_result(
        detections=[make_detection(bbox=(10, 10, 40, 40))],
        frame_index=1,
    )
    second_result = make_frame_result(
        detections=[make_detection(bbox=(12, 10, 42, 40))],
        frame_index=2,
    )

    manager.process_frame_result(first_result)
    manager.process_frame_result(second_result)

    assert summary.total_detection_events == 1
    assert len(summary.events) == 1
    assert summary.class_counts == {"gun": 1}


def test_process_frame_result_creates_new_event_after_track_ttl(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, _ = make_manager(tmp_path)

    first_result = make_frame_result(
        detections=[make_detection(bbox=(10, 10, 40, 40))],
        frame_index=1,
    )
    second_result = make_frame_result(
        detections=[make_detection(bbox=(10, 10, 40, 40))],
        frame_index=20,
    )

    manager.process_frame_result(first_result)
    manager.process_frame_result(second_result)

    assert summary.total_detection_events == 2
    assert len(summary.events) == 2
    assert summary.events[0].event_id == 1
    assert summary.events[1].event_id == 2
    assert summary.class_counts == {"gun": 2}


def test_process_frame_result_saves_multiple_new_detections_as_one_event(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, _ = make_manager(tmp_path)

    detections = [
        make_detection(
            class_id=0,
            class_name="gun",
            bbox=(10, 10, 35, 35),
        ),
        make_detection(
            class_id=1,
            class_name="knife",
            bbox=(50, 10, 80, 35),
        ),
    ]

    result = make_frame_result(detections=detections, frame_index=1)

    manager.process_frame_result(result)

    assert summary.total_detection_events == 1
    assert summary.class_counts == {
        "gun": 1,
        "knife": 1,
    }

    event = summary.events[0]
    assert event.class_ids == [0, 1]
    assert event.class_names == ["gun", "knife"]
    assert event.bboxes == [
        (10, 10, 35, 35),
        (50, 10, 80, 35),
    ]


def test_process_frame_result_treats_same_bbox_but_different_class_as_new_detection(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, _ = make_manager(tmp_path)

    first_result = make_frame_result(
        detections=[
            make_detection(
                class_id=0,
                class_name="gun",
                bbox=(10, 10, 40, 40),
            )
        ],
        frame_index=1,
    )

    second_result = make_frame_result(
        detections=[
            make_detection(
                class_id=1,
                class_name="knife",
                bbox=(10, 10, 40, 40),
            )
        ],
        frame_index=2,
    )

    manager.process_frame_result(first_result)
    manager.process_frame_result(second_result)

    assert summary.total_detection_events == 2
    assert summary.class_counts == {
        "gun": 1,
        "knife": 1,
    }


def test_process_frame_result_saves_detection_after_it_becomes_fully_visible(
    tmp_path,
    monkeypatch,
):
    patch_save_detection_frame(monkeypatch)
    manager, summary, _ = make_manager(tmp_path)

    partially_visible = make_frame_result(
        detections=[
            make_detection(
                bbox=(70, 10, 98, 40),
            )
        ],
        frame_index=1,
        width=100,
    )

    fully_visible = make_frame_result(
        detections=[
            make_detection(
                bbox=(60, 10, 90, 40),
            )
        ],
        frame_index=2,
        width=100,
    )

    manager.process_frame_result(partially_visible)
    manager.process_frame_result(fully_visible)

    assert summary.total_detection_events == 1
    assert len(summary.events) == 1
    assert summary.events[0].frame_index == 2
    assert summary.events[0].bboxes == [(60, 10, 90, 40)]
