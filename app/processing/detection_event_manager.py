from pathlib import Path
from typing import Optional

from app.domain.entities import DetectionEvent, FrameResult, SessionSummary
from app.session.session_results_service import SessionResultsService


class DetectionEventManager:
    def __init__(
        self,
        session_summary: SessionSummary,
        summary_path: str | Path,
        detections_dir: str | Path,
        event_iou_threshold: float = 0.3,
        event_ttl_frames: int = 15,
        right_edge_margin_px: int = 8,
    ):
        self.session_summary = session_summary
        self.summary_path = Path(summary_path)
        self.detections_dir = Path(detections_dir)

        self.event_iou_threshold = float(event_iou_threshold)
        self.event_ttl_frames = int(event_ttl_frames)
        self.right_edge_margin_px = int(right_edge_margin_px)

        self._next_event_id = 1
        self._active_detection_tracks: list[dict] = []

    def process_frame_result(self, result: FrameResult) -> None:
        self._remove_stale_tracks(result.frame_index)

        frame_width = result.frame.shape[1]
        newly_ready_tracks: list[dict] = []

        for det in result.detections:
            track = self._find_matching_track(
                class_id=det.class_id,
                bbox=det.bbox,
                current_frame_index=result.frame_index,
            )

            is_fully_visible = self._is_fully_visible(
                bbox=det.bbox,
                frame_width=frame_width,
            )

            if track is None:
                track = {
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                    "last_bbox": det.bbox,
                    "last_seen_frame": result.frame_index,
                    "saved": False,
                }
                self._active_detection_tracks.append(track)
            else:
                track["class_id"] = det.class_id
                track["class_name"] = det.class_name
                track["last_bbox"] = det.bbox
                track["last_seen_frame"] = result.frame_index

            if not track["saved"] and is_fully_visible:
                track["saved"] = True
                newly_ready_tracks.append(
                    {
                        "class_id": det.class_id,
                        "class_name": det.class_name,
                        "bbox": det.bbox,
                    }
                )

        if not newly_ready_tracks:
            return

        event_id = self._next_event_id

        image_path = SessionResultsService.save_detection_frame(
            frame=result.frame,
            detections_dir=self.detections_dir,
            event_id=event_id,
        )

        event = DetectionEvent(
            event_id=event_id,
            class_ids=[item["class_id"] for item in newly_ready_tracks],
            class_names=[item["class_name"] for item in newly_ready_tracks],
            frame_index=result.frame_index,
            timestamp_sec=result.timestamp_sec,
            image_path=image_path,
            bboxes=[item["bbox"] for item in newly_ready_tracks],
        )

        SessionResultsService.append_detection_event(
            summary=self.session_summary,
            summary_path=self.summary_path,
            event=event,
        )

        self._next_event_id += 1

    def _find_matching_track(
        self,
        class_id: int,
        bbox: tuple[int, int, int, int],
        current_frame_index: int,
    ) -> Optional[dict]:
        best_track = None
        best_iou = 0.0

        for track in self._active_detection_tracks:
            if track["class_id"] != class_id:
                continue

            frame_gap = current_frame_index - track["last_seen_frame"]
            if frame_gap > self.event_ttl_frames:
                continue

            iou = self._compute_iou(bbox, track["last_bbox"])
            if iou >= self.event_iou_threshold and iou > best_iou:
                best_iou = iou
                best_track = track

        return best_track

    def _remove_stale_tracks(self, current_frame_index: int) -> None:
        self._active_detection_tracks = [
            track
            for track in self._active_detection_tracks
            if current_frame_index - track["last_seen_frame"] <= self.event_ttl_frames
        ]

    def _is_fully_visible(
        self,
        bbox: tuple[int, int, int, int],
        frame_width: int,
    ) -> bool:
        _, _, x2, _ = bbox
        return x2 <= frame_width - self.right_edge_margin_px

    @staticmethod
    def _compute_iou(
        box_a: tuple[int, int, int, int],
        box_b: tuple[int, int, int, int],
    ) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)

        union_area = area_a + area_b - inter_area
        if union_area <= 0:
            return 0.0

        return inter_area / union_area
