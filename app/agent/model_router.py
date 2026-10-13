"""Low-compute model routing for SQL generation."""
from typing import List


SMALL_MODEL = "openai/gpt-oss-20b"
STRONG_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.6-27b"


def model_candidates_for(question: str, selected_table_count: int = 0) -> List[str]:
    """Start small for simple BI queries and escalate complex requests."""
    normalized = question.lower()
    complex_markers = (
        "cohort", "retention", "funnel", "correlation", "year over year",
        "month over month", "compare", "previous period", "why", "drivers",
        "percentile", "window", "rolling", "repeat", "lifetime value",
    )
    is_complex = (
        len(question) > 180
        or selected_table_count >= 5
        or any(marker in normalized for marker in complex_markers)
    )
    if is_complex:
        return [STRONG_MODEL, SMALL_MODEL, FALLBACK_MODEL]
    return [SMALL_MODEL, STRONG_MODEL, FALLBACK_MODEL]
