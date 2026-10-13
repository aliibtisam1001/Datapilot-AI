"""Deterministic business semantics derived from known or generic schemas."""
from app.database.schema import DatabaseSchema


def build_semantic_context(db_schema: DatabaseSchema) -> str:
    table_names = set(db_schema.table_names)
    olist_core = {"orders", "order_items", "customers", "products"}
    if olist_core.issubset(table_names):
        return """Business metric definitions for this Olist schema:
- Realized product revenue = SUM(order_items.price) joined to orders and filtered to order_status = 'delivered'. Freight is excluded unless requested.
- A human customer is identified by customers.customer_unique_id; customer_id is order-specific.
- English category names require products joined to product_category_name_translation.
- Purchase time is orders.order_purchase_timestamp; delivery duration uses delivered customer date minus purchase timestamp."""

    financial = []
    time_columns = []
    entity_columns = []
    for table_name, table in db_schema.tables.items():
        for column in table.columns:
            name = column.name.lower()
            qualified = f"{table_name}.{column.name}"
            if any(word in name for word in ("revenue", "amount", "price", "cost", "salary", "value")):
                financial.append(qualified)
            if any(word in name for word in ("date", "time", "created_at", "updated_at")):
                time_columns.append(qualified)
            if name.endswith("_id") and (column.primary_key or "customer" in name or "user" in name):
                entity_columns.append(qualified)

    lines = ["Schema-derived semantic hints (verify against the user's wording):"]
    if financial:
        lines.append("- Candidate financial measures: " + ", ".join(financial[:12]))
    if time_columns:
        lines.append("- Candidate time dimensions: " + ", ".join(time_columns[:12]))
    if entity_columns:
        lines.append("- Candidate entity identifiers: " + ", ".join(entity_columns[:12]))
    return "\n".join(lines)
