"""Deterministic result summaries for common BI result shapes."""
from typing import Optional
from numbers import Integral, Real

import pandas as pd


def _format_value(value) -> str:
    if pd.isna(value):
        return "not available"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Integral):
        return f"{int(value):,}"
    if isinstance(value, Real):
        numeric = float(value)
        return f"{numeric:,.2f}" if not numeric.is_integer() else f"{int(numeric):,}"
    return str(value)


def summarize_result(question: str, df: pd.DataFrame) -> Optional[str]:
    """Summarize simple metrics/rankings without another model invocation."""
    if df is None or df.empty:
        return "No matching records were returned for this question."

    rows, columns = df.shape
    if rows == 1 and columns == 1:
        label = str(df.columns[0]).replace("_", " ")
        return f"{label.title()} is {_format_value(df.iloc[0, 0])}."

    if rows == 1 and columns <= 4:
        metrics = [
            f"{str(column).replace('_', ' ')}: {_format_value(df.iloc[0][column])}"
            for column in df.columns
        ]
        return "The result is " + "; ".join(metrics) + "."

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    non_numeric_columns = [c for c in df.columns if c not in numeric_columns]

    if columns == 2 and len(numeric_columns) == 1 and len(non_numeric_columns) == 1:
        label_column = non_numeric_columns[0]
        value_column = numeric_columns[0]
        first = df.iloc[0]
        label = str(value_column).replace("_", " ")

        time_words = ("date", "month", "year", "week", "quarter", "time", "period")
        if any(word in str(label_column).lower() for word in time_words) and rows > 1:
            start = df.iloc[0][value_column]
            end = df.iloc[-1][value_column]
            try:
                delta = float(end) - float(start)
                pct = (delta / abs(float(start)) * 100) if float(start) else None
                direction = "increased" if delta > 0 else "decreased" if delta < 0 else "was unchanged"
                change = f" ({abs(pct):.1f}%)" if pct is not None else ""
                return (
                    f"{label.title()} {direction}{change}, from {_format_value(start)} "
                    f"in {first[label_column]} to {_format_value(end)} in {df.iloc[-1][label_column]}."
                )
            except (TypeError, ValueError):
                return None

        return (
            f"The leading {str(label_column).replace('_', ' ')} is "
            f"{first[label_column]} with {label} of {_format_value(first[value_column])}. "
            f"The result contains {rows} ranked entries."
        )

    return None
