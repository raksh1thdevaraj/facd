from app.modules.text_consistency.baseline_checker import BaselineAlignmentAnalyzer
from app.modules.text_consistency.font_size_analyzer import FontSizeAnalyzer
from app.modules.text_consistency.format_checker import FormatChecker
from app.modules.text_consistency.logical_validator import LogicalConsistencyValidator
from app.modules.text_consistency.score_aggregator import ScoreAggregator
from app.modules.text_consistency.service import (
    TextConsistencyService,
    get_text_consistency_service,
)
from app.modules.text_consistency.spacing_analyzer import CharacterSpacingAnalyzer
from app.modules.text_consistency.stroke_width_analyzer import StrokeWidthAnalyzer
from app.modules.text_consistency.visualizer import TextAnomalyVisualizer

__all__ = [
    "BaselineAlignmentAnalyzer",
    "FontSizeAnalyzer",
    "StrokeWidthAnalyzer",
    "CharacterSpacingAnalyzer",
    "FormatChecker",
    "LogicalConsistencyValidator",
    "ScoreAggregator",
    "TextAnomalyVisualizer",
    "TextConsistencyService",
    "get_text_consistency_service",
]
