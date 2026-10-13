"""
Schema Selector for DataPilot AI.
Dynamically prunes large database schemas to select only tables and foreign-key
relationships relevant to the user's natural language question.
"""
import re
from collections import deque
from typing import Dict, List, Set
from app.database.schema import DatabaseSchema, TableSchema


BUSINESS_SYNONYMS = {
    "revenue": {"price", "amount", "payment", "sales", "order", "delivered"},
    "sales": {"revenue", "price", "amount", "order", "deal"},
    "category": {"product", "category", "translation"},
    "customer": {"customer", "order", "buyer", "client"},
    "customers": {"customer", "order", "buyer", "client"},
    "repeat": {"customer", "order", "transaction"},
    "delivery": {"order", "customer", "delivered", "shipping", "date"},
    "shipping": {"order", "customer", "delivery", "freight"},
    "review": {"review", "score", "rating", "order"},
    "seller": {"seller", "order", "product"},
    "employee": {"employee", "staff", "department", "salary"},
    "staff": {"employee", "staff", "department", "salary"},
}


class SchemaSelector:
    """Selects relevant subset of tables and relationships from a DatabaseSchema."""

    @classmethod
    def select_relevant_schema(cls, db_schema: DatabaseSchema, question: str, max_tables: int = 8) -> DatabaseSchema:
        """
        Extract a pruned DatabaseSchema containing only tables relevant to the user question.
        Always preserves foreign key connectivity between selected tables.
        """
        all_tables = db_schema.tables
        
        # If schema is small, return full schema without pruning
        if len(all_tables) <= max_tables:
            return db_schema

        question_lower = question.lower()
        tokens = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', question_lower))
        for token in list(tokens):
            if token.endswith("ies") and len(token) > 4:
                tokens.add(token[:-3] + "y")
            elif token.endswith("s") and len(token) > 4:
                tokens.add(token[:-1])
        expanded_tokens = set(tokens)
        for token in tokens:
            expanded_tokens.update(BUSINESS_SYNONYMS.get(token, set()))

        scored_tables = []
        for tname, tschema in all_tables.items():
            score = 0
            tname_lower = tname.lower()
            
            # Exact or partial table-name matches are strongest.
            if tname_lower in question_lower:
                score += 20
            table_parts = set(re.findall(r'[a-z0-9]+', tname_lower))
            for token in expanded_tokens:
                direct = token in tokens
                if token in table_parts:
                    score += 9 if direct else 2
                elif token in tname_lower or tname_lower in token:
                    score += 6 if direct else 1
            
            # Column name matches
            for col in tschema.columns:
                col_name_lower = col.name.lower()
                if col_name_lower in question_lower:
                    score += 4
                col_parts = set(re.findall(r'[a-z0-9]+', col_name_lower))
                for token in expanded_tokens:
                    direct = token in tokens
                    if token in col_parts:
                        score += 5 if direct else 1
                    elif token in col_name_lower or col_name_lower in token:
                        score += 3 if direct else 0

            column_names = {column.name.lower() for column in tschema.columns}
            if "category" in tokens:
                if any("category" in name for name in column_names):
                    score += 25
                if "translation" in tname_lower:
                    score += 12
            if "revenue" in tokens or "sales" in tokens:
                if any(
                    any(metric in name for metric in ("price", "revenue", "amount", "payment_value"))
                    for name in column_names
                ):
                    score += 22
            if "delivered" in tokens and "order_status" in column_names:
                score += 25
            if "repeat" in tokens:
                if "customer_unique_id" in column_names or "order_id" in column_names:
                    score += 16

            scored_tables.append((score, tname))

        # Sort by relevance score
        scored_tables.sort(key=lambda item: (-item[0], item[1]))

        # Use a small set of high-signal seeds, leaving space for bridge tables.
        seed_budget = max(2, min(max_tables, max_tables // 2))
        selected = [name for score, name in scored_tables if score > 0][:seed_budget]
        if len(selected) < 2:
            selected = [name for _, name in scored_tables[: min(2, max_tables)]]

        # Add the shortest FK paths between seeds instead of merely adding all
        # one-hop neighbors. This preserves bridge tables while staying compact.
        final_table_names: Set[str] = set(selected)
        for index, source in enumerate(selected):
            for target in selected[index + 1:]:
                path = cls._shortest_relationship_path(db_schema, source, target)
                if path and len(final_table_names.union(path)) <= max_tables:
                    final_table_names.update(path)

        score_lookup = {name: score for score, name in scored_tables}
        final_tables_list = sorted(
            final_table_names,
            key=lambda name: (-score_lookup.get(name, 0), name),
        )[:max_tables]
        
        pruned_tables = {name: all_tables[name] for name in final_tables_list if name in all_tables}
        
        # Prune relationships to only those connecting the selected tables
        pruned_relationships = [
            rel for rel in db_schema.relationships
            if rel.from_table in pruned_tables and rel.to_table in pruned_tables
        ]

        return DatabaseSchema(
            dialect=db_schema.dialect,
            tables=pruned_tables,
            relationships=pruned_relationships,
        )

    @staticmethod
    def _shortest_relationship_path(
        db_schema: DatabaseSchema,
        source: str,
        target: str,
    ) -> List[str]:
        """Return the shortest undirected FK path between two tables."""
        if source == target:
            return [source]

        graph: Dict[str, Set[str]] = {name: set() for name in db_schema.tables}
        for rel in db_schema.relationships:
            if rel.from_table in graph and rel.to_table in graph:
                graph[rel.from_table].add(rel.to_table)
                graph[rel.to_table].add(rel.from_table)

        queue = deque([(source, [source])])
        visited = {source}
        while queue:
            node, path = queue.popleft()
            for neighbor in sorted(graph.get(node, set())):
                if neighbor in visited:
                    continue
                next_path = path + [neighbor]
                if neighbor == target:
                    return next_path
                visited.add(neighbor)
                queue.append((neighbor, next_path))
        return []


def select_relevant_schema(db_schema: DatabaseSchema, question: str, max_tables: int = 8) -> DatabaseSchema:
    """Convenience helper for schema selection."""
    return SchemaSelector.select_relevant_schema(db_schema, question, max_tables=max_tables)
