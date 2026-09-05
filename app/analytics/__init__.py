"""
Analytics Package for DataPilot AI.
Exports MetricDiscoveryEngine, discover_kpis, ExecutiveInsightsEngine,
and generate_executive_briefing.
"""
from app.analytics.metrics import (
    MetricDiscoveryEngine,
    discover_kpis,
)
from app.analytics.insights import (
    ExecutiveInsightsEngine,
    generate_executive_briefing,
)

__all__ = [
    "MetricDiscoveryEngine",
    "discover_kpis",
    "ExecutiveInsightsEngine",
    "generate_executive_briefing",
]
