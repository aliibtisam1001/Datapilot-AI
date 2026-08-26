"""
Proactive Business Intelligence & Executive Insights Engine for DataPilot AI.
Analyzes connected database metrics to synthesize high-level strategic takeaways,
growth opportunities, and operational performance briefings.
"""
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.engine import Engine
from langchain_groq import ChatGroq

from app.database.schema import DatabaseSchema
from app.analytics.metrics import MetricDiscoveryEngine
from app.utils import strip_thinking


class ExecutiveInsightsEngine:
    """Generates structured proactive executive briefings from database schema and live metrics."""

    @classmethod
    def generate_executive_briefing(
        cls,
        engine: Engine,
        db_schema: DatabaseSchema,
        llm: Optional[ChatGroq] = None,
        api_key: Optional[str] = None,
        model_name: str = "openai/gpt-oss-120b",
    ) -> List[Dict[str, str]]:
        """
        Produce 3 structured executive takeaway cards from the connected database.
        """
        kpis = MetricDiscoveryEngine.discover_kpis(engine, db_schema)
        kpi_text = "\n".join([f"- {k['title']}: {k['value']} ({k['delta']})" for k in kpis])

        prompt = f"""You are a Chief Analytics Officer and Executive Strategy Advisor.
Analyze the following live database metrics and schema to produce 3 concise strategic insights for executive leadership.

Database Dialect: {db_schema.dialect.upper()}
Database Tables: {', '.join(db_schema.table_names)}

Key Live Discovered Metrics:
{kpi_text}

Provide exactly 3 distinct strategic takeaways:
1. Category/Entity Performance Leader (Key volume driver)
2. Growth & Transaction Health (Trends and operational velocity)
3. Operational Focus & Optimization (Efficiency, margin, or risk area)

Format as:
TITLE: <Short bold title>
SUMMARY: <2-sentence executive summary with specific numbers if available>
---
TITLE: <Short bold title>
SUMMARY: <2-sentence executive summary>
---
TITLE: <Short bold title>
SUMMARY: <2-sentence executive summary>"""

        if llm is None:
            llm = ChatGroq(
                model=model_name,
                temperature=0.3,
                api_key=api_key or os.getenv("GROQ_API_KEY"),
            )

        try:
            res = llm.invoke(prompt)
            raw = strip_thinking(res.content if hasattr(res, "content") else str(res))
            return cls._parse_briefing(raw, kpis)
        except Exception:
            return cls._fallback_briefing(kpis, db_schema)

    @staticmethod
    def _parse_briefing(raw_text: str, kpis: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Parse structured text from LLM response into insight items."""
        insights = []
        blocks = raw_text.split("---")
        for b in blocks:
            lines = [line.strip() for line in b.strip().split("\n") if line.strip()]
            title = ""
            summary = ""
            for l in lines:
                if l.upper().startswith("TITLE:"):
                    title = l[6:].strip().strip("*")
                elif l.upper().startswith("SUMMARY:"):
                    summary = l[8:].strip()
                elif not title and not l.startswith("#"):
                    title = l.strip("*")
                elif title and not summary:
                    summary += " " + l

            if title and summary:
                insights.append({
                    "title": title,
                    "summary": summary,
                    "tag": "STRATEGIC TAKEAWAY",
                })

        if len(insights) >= 3:
            return insights[:3]
        return ExecutiveInsightsEngine._fallback_briefing(kpis, None)

    @staticmethod
    def _fallback_briefing(kpis: List[Dict[str, Any]], db_schema: Optional[DatabaseSchema]) -> List[Dict[str, str]]:
        """Deterministic fallback briefing when LLM is unavailable."""
        first_kpi = kpis[0]["title"] + ": " + kpis[0]["value"] if kpis else "Active Database Connected"
        second_kpi = kpis[1]["title"] + ": " + kpis[1]["value"] if len(kpis) > 1 else "Normalized relational schema"
        
        return [
            {
                "title": "Primary Transaction Volume Driver",
                "summary": f"The connected database reflects robust transaction volume ({first_kpi}) across core relational tables.",
                "tag": "VOLUME LEADER",
            },
            {
                "title": "Entity Aggregate Health",
                "summary": f"Key financial and operational aggregates ({second_kpi}) demonstrate stable data consistency across connected tables.",
                "tag": "FINANCIAL HEALTH",
            },
            {
                "title": "Automated Schema Synchronization",
                "summary": "Full schema metadata, foreign key relationships, and query routing pipelines are synchronized and ready for natural language exploration.",
                "tag": "DATA PIPELINE",
            },
        ]


def generate_executive_briefing(
    engine: Engine,
    db_schema: DatabaseSchema,
    llm: Optional[ChatGroq] = None,
    api_key: Optional[str] = None,
    model_name: str = "openai/gpt-oss-120b",
) -> List[Dict[str, str]]:
    return ExecutiveInsightsEngine.generate_executive_briefing(
        engine, db_schema, llm=llm, api_key=api_key, model_name=model_name
    )
