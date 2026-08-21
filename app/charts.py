"""
Module 10 - Auto-Chart Layer.
Inspects a DataFrame's shape and content to automatically pick
the most appropriate Plotly chart type.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def auto_chart(df: pd.DataFrame, question: str = "") -> Optional[go.Figure]:
    """
    Automatically generate an appropriate Plotly chart based on DataFrame shape.

    Logic:
        - Single scalar value → Big metric indicator
        - Single row, multiple columns → Horizontal bar (comparing metrics)
        - Two columns (category + numeric) → Vertical bar chart
        - Two columns (date/time + numeric) → Line chart
        - Multiple rows, multiple numeric columns → Grouped bar chart
        - Otherwise → Table display

    Args:
        df: The query result DataFrame.
        question: The original question (used for chart title).

    Returns:
        A Plotly Figure, or None if no chart is appropriate.
    """
    if df is None or df.empty:
        return _make_empty_fig("No data to display")

    rows, cols = df.shape
    question_lower = question.lower()

    # ── Case 1: Single scalar value → Metric indicator ──
    if rows == 1 and cols == 1:
        value = df.iloc[0, 0]
        label = df.columns[0]
        return _make_metric(value, label, question)

    # ── Case 2: Single row, few columns → Metric cards ──
    if rows == 1 and cols <= 4:
        return _make_multi_metric(df, question)

    # Identify column types
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

    # ── Case 3: Two columns — one categorical, one numeric ──
    if cols == 2 and len(numeric_cols) == 1 and len(non_numeric_cols) == 1:
        cat_col = non_numeric_cols[0]
        val_col = numeric_cols[0]

        # Check if the categorical column looks like dates/months
        if _is_time_like(df[cat_col], cat_col):
            fig = px.line(
                df, x=cat_col, y=val_col,
                title=question or f"{val_col} over {cat_col}",
                markers=True,
            )
            _style_fig(fig)
            return fig
        else:
            fig = px.bar(
                df, x=cat_col, y=val_col,
                title=question or f"{val_col} by {cat_col}",
                text_auto=True,
            )
            _style_fig(fig)
            return fig

    # ── Case 4: Multiple numeric columns with one category column ──
    if len(non_numeric_cols) == 1 and len(numeric_cols) >= 2:
        cat_col = non_numeric_cols[0]
        df_melted = df.melt(id_vars=cat_col, value_vars=numeric_cols,
                            var_name='Metric', value_name='Value')
        fig = px.bar(
            df_melted, x=cat_col, y='Value', color='Metric',
            barmode='group',
            title=question or "Comparison",
        )
        _style_fig(fig)
        return fig

    # ── Case 5: All numeric, multiple rows → bar chart on index ──
    if len(numeric_cols) == cols and rows > 1:
        fig = px.bar(
            df, y=numeric_cols[0],
            title=question or f"Distribution of {numeric_cols[0]}",
            text_auto=True,
        )
        _style_fig(fig)
        return fig

    # ── Fallback: Table display ──
    return _make_table(df, question)


def _is_time_like(series: pd.Series, col_name: str) -> bool:
    """Heuristic: does this column represent time/dates?"""
    name_lower = col_name.lower()
    time_keywords = ['date', 'month', 'year', 'quarter', 'week', 'day',
                     'timestamp', 'time', 'period']
    if any(kw in name_lower for kw in time_keywords):
        return True
    # Check if values look like dates or month numbers
    try:
        sample = series.head(5).astype(str)
        if all(len(s) in (2, 4, 7, 10, 19) for s in sample):
            # Could be month (01-12), year (2018), date (2018-01), etc.
            try:
                pd.to_datetime(series)
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False


VIBRANT_PALETTE = [
    "#8B5CF6",  # Electric Violet
    "#E879F9",  # Neon Fuchsia
    "#D946EF",  # Vivid Magenta
    "#A855F7",  # Vivid Purple
    "#F472B6",  # Rose Pink
    "#C084FC",  # Soft Violet
    "#10B981",  # Emerald Green
    "#F59E0B",  # Amber Orange
]


def _make_metric(value, label: str, title: str = "") -> go.Figure:
    """Create a futuristic glowing 3D glass metric card."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = None

    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number",
        value=numeric_value,
        number={
            "font": {"size": 58, "color": "#8B5CF6", "family": "Space Grotesk, sans-serif"},
            "valueformat": ",.2f" if isinstance(numeric_value, float) and abs(numeric_value) > 1000 else ",g"
        },
        title={
            "text": f"<span style='font-size:15px; color:#94A3B8; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;'>{label}</span>",
            "font": {"family": "IBM Plex Mono, monospace"}
        },
    ))
    fig.update_layout(
        title=dict(
            text=f"<span style='color:#F8FAFC; font-weight:700;'>{title}</span>" if title else "",
            font=dict(size=16, family="Space Grotesk, sans-serif")
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.75)",
        plot_bgcolor="rgba(15, 23, 42, 0.75)",
        height=240,
        margin=dict(l=20, r=20, t=45, b=20),
        transition=dict(duration=600, easing="cubic-in-out"),
    )
    return fig


def _make_multi_metric(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create multi-metric cards with distinct violet & fuchsia colors."""
    fig = go.Figure()
    n_cols = len(df.columns)
    colors = ["#8B5CF6", "#E879F9", "#D946EF", "#F59E0B"]

    for i, col in enumerate(df.columns):
        val = df.iloc[0][col]
        try:
            numeric_val = float(val)
        except (TypeError, ValueError):
            numeric_val = None
        
        color = colors[i % len(colors)]
        fig.add_trace(go.Indicator(
            mode="number",
            value=numeric_val,
            number={
                "font": {"size": 40, "color": color, "family": "Space Grotesk, sans-serif"},
                "valueformat": ",.2f" if isinstance(numeric_val, float) and abs(numeric_val) > 1000 else ",g"
            },
            title={
                "text": f"<span style='font-size:13px; color:#94A3B8; font-weight:600; text-transform:uppercase;'>{col}</span>",
                "font": {"family": "IBM Plex Mono, monospace"}
            },
            domain={'x': [i / n_cols, (i + 1) / n_cols], 'y': [0, 1]},
        ))

    fig.update_layout(
        title=dict(
            text=f"<span style='color:#F8FAFC; font-weight:700;'>{title}</span>" if title else "",
            font=dict(size=16, family="Space Grotesk, sans-serif")
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.75)",
        plot_bgcolor="rgba(15, 23, 42, 0.75)",
        height=220,
        margin=dict(l=20, r=20, t=45, b=20),
        transition=dict(duration=600, easing="cubic-in-out"),
    )
    return fig


def _make_table(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a styled neon-accented glass table for complex data."""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in df.columns],
            fill_color='#1E293B',
            font=dict(color='#E879F9', size=13, family="Space Grotesk, sans-serif"),
            align='left',
            height=34,
            line_color='#334155',
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='rgba(15, 23, 42, 0.85)',
            font=dict(color='#F1F5F9', size=12, family="IBM Plex Mono, monospace"),
            align='left',
            height=28,
            line_color='#1E293B',
        ),
    )])
    fig.update_layout(
        title=dict(
            text=f"<span style='color:#F8FAFC; font-weight:700;'>{title}</span>" if title else "",
            font=dict(size=16, family="Space Grotesk, sans-serif")
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.75)",
        margin=dict(l=10, r=10, t=45, b=10),
        height=min(400, 60 + 32 * len(df)),
    )
    return fig


def _make_empty_fig(message: str) -> go.Figure:
    """Create a figure showing a 'no data' message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#64748B", family="IBM Plex Sans, sans-serif"),
    )
    fig.update_layout(
        paper_bgcolor="rgba(15, 23, 42, 0.75)", plot_bgcolor="rgba(15, 23, 42, 0.75)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=180,
    )
    return fig


def _style_fig(fig: go.Figure):
    """Apply consistent high-contrast 3D glowing glassmorphism theme styling."""
    fig.update_layout(
        paper_bgcolor="rgba(15, 23, 42, 0.85)",
        plot_bgcolor="rgba(11, 17, 33, 0.6)",
        font=dict(color="#F1F5F9", family="IBM Plex Sans, sans-serif"),
        title_font=dict(size=16, color="#F8FAFC", family="Space Grotesk, sans-serif"),
        margin=dict(l=45, r=30, t=55, b=45),
        transition=dict(duration=700, easing="cubic-in-out"),
        xaxis=dict(
            gridcolor="rgba(51, 65, 85, 0.4)",
            linecolor="rgba(71, 85, 105, 0.6)",
            tickfont=dict(family="IBM Plex Mono, monospace", size=11, color="#94A3B8"),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="rgba(51, 65, 85, 0.4)",
            linecolor="rgba(71, 85, 105, 0.6)",
            tickfont=dict(family="IBM Plex Mono, monospace", size=11, color="#94A3B8"),
            showgrid=True,
        ),
    )

    # Style bar traces with colorful palette
    for i, trace in enumerate(fig.data):
        if trace.type == "bar":
            # If multiple bars in a single trace, apply distinct colors per bar
            n_bars = len(trace.x) if trace.x is not None else 1
            bar_colors = [VIBRANT_PALETTE[j % len(VIBRANT_PALETTE)] for j in range(n_bars)]
            trace.marker = dict(
                color=bar_colors if n_bars > 1 else VIBRANT_PALETTE[i % len(VIBRANT_PALETTE)],
                line=dict(color="rgba(255,255,255,0.25)", width=1.5),
                cornerradius=6,
            )
            trace.textfont = dict(family="IBM Plex Mono, monospace", size=11, color="#FFFFFF")
        elif trace.type == "scatter":
            trace.line = dict(color="#8B5CF6", width=3, shape="spline")
            trace.marker = dict(color="#E879F9", size=8, line=dict(color="#FFFFFF", width=2))


# ============================================================
# Test when run directly
# ============================================================
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import sqlite3
    import os

    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
    CHARTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tests', 'charts')
    os.makedirs(CHARTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    test_cases = [
        {
            "name": "single_metric",
            "question": "How many total orders are there?",
            "sql": "SELECT COUNT(*) as total_orders FROM orders",
            "expected_chart": "Metric indicator (single value)",
        },
        {
            "name": "category_bar",
            "question": "Top 5 product categories by revenue",
            "sql": """
                SELECT t.product_category_name_english as category,
                       ROUND(SUM(oi.price), 2) as revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN product_category_name_translation t
                    ON p.product_category_name = t.product_category_name
                GROUP BY t.product_category_name_english
                ORDER BY revenue DESC LIMIT 5
            """,
            "expected_chart": "Vertical bar chart",
        },
        {
            "name": "time_series",
            "question": "Monthly order count in 2018",
            "sql": """
                SELECT strftime('%Y-%m', order_purchase_timestamp) as month,
                       COUNT(*) as order_count
                FROM orders
                WHERE strftime('%Y', order_purchase_timestamp) = '2018'
                GROUP BY month ORDER BY month
            """,
            "expected_chart": "Line chart (time series)",
        },
        {
            "name": "multi_metric",
            "question": "Canceled orders count and percentage",
            "sql": """
                SELECT SUM(CASE WHEN order_status='canceled' THEN 1 ELSE 0 END) as canceled,
                       COUNT(*) as total,
                       ROUND(100.0*SUM(CASE WHEN order_status='canceled' THEN 1 ELSE 0 END)/COUNT(*),2) as cancel_pct
                FROM orders
            """,
            "expected_chart": "Multi-metric indicator",
        },
    ]

    print("=" * 60)
    print("MODULE 10 - Auto-Chart Layer Tests")
    print("=" * 60)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {tc['question']}")
        print(f"Expected chart type: {tc['expected_chart']}")

        df = pd.read_sql(tc["sql"], conn)
        print(f"Data shape: {df.shape}")
        print(f"Data:\n{df.to_string(index=False)}")

        fig = auto_chart(df, tc["question"])

        if fig is not None:
            chart_path = os.path.join(CHARTS_DIR, f"{tc['name']}.html")
            fig.write_html(chart_path)
            print(f"Chart type: {fig.data[0].__class__.__name__}")
            print(f"Saved to: {os.path.abspath(chart_path)}")
            print(f"Status: OK")
        else:
            print(f"Status: No chart generated")

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"All charts saved to: {os.path.abspath(CHARTS_DIR)}")
    print(f"Open any .html file in a browser to view the chart.")
    print(f"{'=' * 60}")
