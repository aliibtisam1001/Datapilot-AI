"""
Analytics Package for DataPilot AI.
Exports MetricDiscoveryEngine, discover_kpis, generate_suggested_questions,
ExecutiveInsightsEngine, and generate_executive_briefing.
"""
from app.analytics.metrics import (
    MetricDiscoveryEngine,
    discover_kpis,
    generate_suggested_questions,
)
from app.analytics.insights import (
    ExecutiveInsightsEngine,
    generate_executive_briefing,
)

__all__ = [
    "MetricDiscoveryEngine",
    "discover_kpis",
    "generate_suggested_questions",
    "ExecutiveInsightsEngine",
    "generate_executive_briefing",
]
