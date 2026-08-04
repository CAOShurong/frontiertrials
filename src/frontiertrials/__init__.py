"""FrontierTrials: no-API blind evaluation for AI web-app outputs."""

__version__ = "0.1.0"

from .analysis import analyze_trial
from .audit import audit_trial
from .report import build_report
from .workspace import Trial

__all__ = ["Trial", "analyze_trial", "audit_trial", "build_report"]
