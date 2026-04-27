from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.session.analysis_session import AnalysisSession

__all__ = ["AnalysisSession"]


def __getattr__(name: str) -> Any:
    if name == "AnalysisSession":
        from app.session.analysis_session import AnalysisSession

        return AnalysisSession

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
