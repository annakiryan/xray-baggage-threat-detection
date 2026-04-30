from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from app.video.capture_service import CaptureService


def test_ensure_results_dir_creates_directory(tmp_path):
    results_dir = tmp_path / "results"

    result = CaptureService.ensure_results_dir(results_dir)

    assert result == results_dir
    assert results_dir.exists()
    assert results_dir.is_dir()


def test_ensure_results_dir_returns_existing_directory(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    result = CaptureService.ensure_results_dir(results_dir)

    assert result == results_dir
    assert results_dir.exists()


def test_add_timestamp_overlay_raises_if_frame_is_none():
    with pytest.raises(ValueError, match="Пустой кадр"):
        CaptureService.add_timestamp_overlay(None, "Дата и время: test")


def test_add_timestamp_overlay_draws_bottom_bar_and_calls_draw_text(monkeypatch):
    calls = {}

    def fake_draw_text_pil(frame, text, position, font_size, text_color):
        calls["frame"] = frame
        calls["text"] = text
        calls["position"] = position
        calls["font_size"] = font_size
        calls["text_color"] = text_color
        return frame

    monkeypatch.setattr(
        "app.video.capture_service.draw_text_pil",
        fake_draw_text_pil,
    )

    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    result = CaptureService.add_timestamp_overlay(
        frame,
        "Дата и время: 30.04.2026 10:00:00",
    )

    assert result.shape == frame.shape
    assert calls["text"] == "Дата и время: 30.04.2026 10:00:00"
    assert calls["position"] == (12, 64)
    assert calls["font_size"] == 24
    assert calls["text_color"] == (255, 255, 255)

    assert np.array_equal(frame, np.zeros((100, 200, 3), dtype=np.uint8))
    assert (result[99, 10] == np.array([30, 30, 30], dtype=np.uint8)).all()


def test_save_frame_with_overlay_raises_if_frame_is_none(tmp_path):
    with pytest.raises(ValueError, match="Нет кадра"):
        CaptureService.save_frame_with_overlay(
            frame=None,
            results_dir=tmp_path,
        )


def test_save_frame_with_overlay_saves_file_with_prefix(monkeypatch, tmp_path):
    calls = {}

    fixed_now = datetime(2026, 4, 30, 10, 20, 30)

    class FakeDateTime:
        @staticmethod
        def now():
            return fixed_now

    def fake_add_timestamp_overlay(frame, timestamp_text):
        calls["timestamp_text"] = timestamp_text
        return frame

    def fake_imwrite(path, frame):
        calls["saved_path"] = path
        calls["saved_frame"] = frame
        Path(path).write_bytes(b"fake image")
        return True

    monkeypatch.setattr("app.video.capture_service.datetime", FakeDateTime)
    monkeypatch.setattr(
        CaptureService,
        "add_timestamp_overlay",
        staticmethod(fake_add_timestamp_overlay),
    )
    monkeypatch.setattr("app.video.capture_service.cv2.imwrite", fake_imwrite)

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    result = CaptureService.save_frame_with_overlay(
        frame=frame,
        results_dir=tmp_path,
        file_prefix="capture",
    )

    expected_path = tmp_path / "capture_2026-04-30_10-20-30.jpg"

    assert result == expected_path
    assert expected_path.exists()
    assert calls["timestamp_text"] == "Дата и время: 30.04.2026 10:20:30"
    assert calls["saved_path"] == str(expected_path)
    assert calls["saved_frame"] is frame


def test_save_frame_with_overlay_saves_file_without_prefix(monkeypatch, tmp_path):
    fixed_now = datetime(2026, 4, 30, 10, 20, 30)

    class FakeDateTime:
        @staticmethod
        def now():
            return fixed_now

    def fake_add_timestamp_overlay(frame, timestamp_text):
        return frame

    def fake_imwrite(path, frame):
        Path(path).write_bytes(b"fake image")
        return True

    monkeypatch.setattr("app.video.capture_service.datetime", FakeDateTime)
    monkeypatch.setattr(
        CaptureService,
        "add_timestamp_overlay",
        staticmethod(fake_add_timestamp_overlay),
    )
    monkeypatch.setattr("app.video.capture_service.cv2.imwrite", fake_imwrite)

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    result = CaptureService.save_frame_with_overlay(
        frame=frame,
        results_dir=tmp_path,
        file_prefix="   ",
    )

    expected_path = tmp_path / "2026-04-30_10-20-30.jpg"

    assert result == expected_path
    assert expected_path.exists()


def test_save_frame_with_overlay_raises_if_cv2_imwrite_failed(monkeypatch, tmp_path):
    fixed_now = datetime(2026, 4, 30, 10, 20, 30)

    class FakeDateTime:
        @staticmethod
        def now():
            return fixed_now

    def fake_add_timestamp_overlay(frame, timestamp_text):
        return frame

    def fake_imwrite(path, frame):
        return False

    monkeypatch.setattr("app.video.capture_service.datetime", FakeDateTime)
    monkeypatch.setattr(
        CaptureService,
        "add_timestamp_overlay",
        staticmethod(fake_add_timestamp_overlay),
    )
    monkeypatch.setattr("app.video.capture_service.cv2.imwrite", fake_imwrite)

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError, match="Не удалось сохранить кадр"):
        CaptureService.save_frame_with_overlay(
            frame=frame,
            results_dir=tmp_path,
            file_prefix="capture",
        )


def test_save_frame_calls_save_frame_with_overlay(monkeypatch, tmp_path):
    calls = {}

    def fake_save_frame_with_overlay(frame, results_dir, file_prefix):
        calls["frame"] = frame
        calls["results_dir"] = results_dir
        calls["file_prefix"] = file_prefix
        return Path(results_dir) / "saved.jpg"

    monkeypatch.setattr(
        CaptureService,
        "save_frame_with_overlay",
        staticmethod(fake_save_frame_with_overlay),
    )

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    result = CaptureService.save_frame(frame, results_dir=tmp_path)

    assert result == tmp_path / "saved.jpg"
    assert calls["frame"] is frame
    assert calls["results_dir"] == tmp_path
    assert calls["file_prefix"] == ""
