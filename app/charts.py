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


def _make_metric(value, label: str, title: str = "") -> go.Figure:
    """Create a big number indicator for a single value."""
    # Convert numpy types to native Python types
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = None

    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number",
        value=numeric_value,
        number={"font": {"size": 60, "color": "#4FC3F7"}},
        title={"text": label, "font": {"size": 18, "color": "#B0BEC5"}},
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        height=300,
    )
    return fig


def _make_multi_metric(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create metric cards for a single-row DataFrame with multiple columns."""
    fig = go.Figure()
    n_cols = len(df.columns)

    for i, col in enumerate(df.columns):
        val = df.iloc[0][col]
        try:
            numeric_val = float(val)
        except (TypeError, ValueError):
            numeric_val = None
        fig.add_trace(go.Indicator(
            mode="number",
            value=numeric_val,
            number={"font": {"size": 40, "color": "#4FC3F7"}},
            title={"text": col, "font": {"size": 14, "color": "#B0BEC5"}},
            domain={'x': [i / n_cols, (i + 1) / n_cols], 'y': [0, 1]},
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        height=250,
    )
    return fig


def _make_table(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a styled Plotly table for complex data."""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='#16213e',
            font=dict(color='white', size=13),
            align='left',
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='#1a1a2e',
            font=dict(color='#e0e0e0', size=12),
            align='left',
        ),
    )])
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='white')),
        paper_bgcolor="#1a1a2e",
        height=min(400, 50 + 30 * len(df)),
    )
    return fig


def _make_empty_fig(message: str) -> go.Figure:
    """Create a figure showing a 'no data' message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=20, color="#B0BEC5"),
    )
    fig.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=200,
    )
    return fig


def _style_fig(fig: go.Figure):
    """Apply consistent dark theme styling."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"),
        title_font=dict(size=16),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_traces(
        marker_color="#4FC3F7",
        selector=dict(type="bar"),
    )


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
