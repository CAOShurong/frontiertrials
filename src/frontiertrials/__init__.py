"""FrontierTrials: private personal and study-grade AI product evaluation."""

__version__ = "0.3.1"

from .adjudication import build_adjudication_queue
from .analysis import analyze_trial
from .audit import audit_trial
from .report import build_report
from .workspace import Trial

__all__ = [
    "Trial",
    "analyze_trial",
    "audit_trial",
    "build_adjudication_queue",
    "build_report",
]
