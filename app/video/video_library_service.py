from pathlib import Path


class VideoLibraryService:
    VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

    @staticmethod
    def load_videos(videos_dir: str | Path) -> list[Path]:
        path = Path(videos_dir)

        if not path.exists() or not path.is_dir():
            return []

        videos = [
            item
            for item in path.iterdir()
            if item.is_file()
            and item.suffix.lower() in VideoLibraryService.VIDEO_SUFFIXES
        ]

        return sorted(videos, key=lambda item: item.name.lower())
