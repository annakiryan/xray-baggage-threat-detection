from app.video.video_library_service import VideoLibraryService


def test_load_videos_returns_empty_list_if_directory_does_not_exist(tmp_path):
    videos_dir = tmp_path / "missing"

    result = VideoLibraryService.load_videos(videos_dir)

    assert result == []


def test_load_videos_returns_empty_list_if_path_is_not_directory(tmp_path):
    file_path = tmp_path / "videos.txt"
    file_path.write_text("not a directory", encoding="utf-8")

    result = VideoLibraryService.load_videos(file_path)

    assert result == []


def test_load_videos_returns_only_supported_video_files(tmp_path):
    (tmp_path / "video.mp4").write_text("", encoding="utf-8")
    (tmp_path / "clip.avi").write_text("", encoding="utf-8")
    (tmp_path / "movie.mkv").write_text("", encoding="utf-8")
    (tmp_path / "image.jpg").write_text("", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("", encoding="utf-8")

    result = VideoLibraryService.load_videos(tmp_path)

    result_names = [path.name for path in result]

    assert result_names == ["clip.avi", "movie.mkv", "video.mp4"]


def test_load_videos_is_case_insensitive_for_suffixes(tmp_path):
    (tmp_path / "A.MP4").write_text("", encoding="utf-8")
    (tmp_path / "B.MOV").write_text("", encoding="utf-8")
    (tmp_path / "C.WEBM").write_text("", encoding="utf-8")

    result = VideoLibraryService.load_videos(tmp_path)

    result_names = [path.name for path in result]

    assert result_names == ["A.MP4", "B.MOV", "C.WEBM"]


def test_load_videos_ignores_directories_with_video_suffix(tmp_path):
    (tmp_path / "folder.mp4").mkdir()
    (tmp_path / "real_video.mp4").write_text("", encoding="utf-8")

    result = VideoLibraryService.load_videos(tmp_path)

    result_names = [path.name for path in result]

    assert result_names == ["real_video.mp4"]
