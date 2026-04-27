from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.config.app.app_config_service import ConfigService
from app.config.interface.interface_settings_service import InterfaceSettingsService
from app.config.model.model_config_service import ModelConfigService
from app.config.interface.theme_palette_service import ThemePaletteService
from app.domain.entities import AppConfig, ModelConfig
from app.domain.settings import (
    DrawingSettings,
    InferenceSettings,
    InterfaceSettings,
    StorageSettings,
)
from app.config.interface.theme_manager import ThemeManager
from app.video.video_library_service import VideoLibraryService

if TYPE_CHECKING:
    from app.ui.main_window.main_window import MainWindow


APP_CONFIG_PATH = Path("configs/app_config.json")
INTERFACE_SETTINGS_PATH = Path("configs/interface_settings.json")
THEME_PALETTES_PATH = Path("configs/theme_palettes.json")


@dataclass(frozen=True)
class AppDependencies:
    app_config: AppConfig
    available_videos: list[Path]
    default_video_path: Path
    model_config: ModelConfig
    interface_settings_service: InterfaceSettingsService
    interface_settings: InterfaceSettings
    theme_manager: ThemeManager


def build_dependencies() -> AppDependencies:
    app_config = ConfigService.load_app_config(APP_CONFIG_PATH)

    available_videos = VideoLibraryService.load_videos(app_config.videos_dir)
    default_video_path = Path(app_config.videos_dir) / app_config.default_video

    model_config_path = Path(app_config.models_dir) / app_config.model_config
    model_config = ModelConfigService.load_model_config(model_config_path)

    interface_settings_service = InterfaceSettingsService(INTERFACE_SETTINGS_PATH)
    interface_settings = interface_settings_service.load()
    theme_palettes = ThemePaletteService.load(THEME_PALETTES_PATH)
    theme_manager = ThemeManager(theme_palettes)

    return AppDependencies(
        app_config=app_config,
        available_videos=available_videos,
        default_video_path=default_video_path,
        model_config=model_config,
        interface_settings_service=interface_settings_service,
        interface_settings=interface_settings,
        theme_manager=theme_manager,
    )


def create_main_window(deps: AppDependencies | None = None) -> "MainWindow":
    from app.session.analysis_session import AnalysisSession
    from app.ui.analysis.analysis_page import AnalysisPage
    from app.ui.history.history_page import HistoryPage
    from app.ui.main_window.main_window import MainWindow
    from app.ui.settings.settings_page import SettingsPage

    dependencies = deps or build_dependencies()

    analysis_session = AnalysisSession(
        model_config=dependencies.model_config,
        storage_settings=StorageSettings(
            default_video_path=dependencies.default_video_path,
            logs_dir=dependencies.app_config.logs_dir,
            results_dir=dependencies.app_config.results_dir,
        ),
        inference_settings=InferenceSettings(
            device=dependencies.app_config.device,
            confidence_threshold=dependencies.app_config.default_confidence_threshold,
            iou_threshold=dependencies.app_config.default_iou_threshold,
            frame_skip=dependencies.app_config.default_frame_skip,
        ),
        drawing_settings=DrawingSettings(enabled=True),
    )

    analysis_page = AnalysisPage(
        session=analysis_session,
        available_videos=dependencies.available_videos,
        default_video=dependencies.app_config.default_video,
    )
    history_page = HistoryPage(results_dir=dependencies.app_config.results_dir)
    settings_page = SettingsPage(
        settings=dependencies.interface_settings,
        settings_service=dependencies.interface_settings_service,
        theme_manager=dependencies.theme_manager,
    )

    return MainWindow(
        analysis_page=analysis_page,
        history_page=history_page,
        settings_page=settings_page,
        session=analysis_session,
        interface_settings=dependencies.interface_settings,
        theme_manager=dependencies.theme_manager,
    )
