"""
Schema Selector for DataPilot AI.
Dynamically prunes large database schemas to select only tables and foreign-key
relationships relevant to the user's natural language question.
"""
import re
from typing import List, Set, Optional
from app.database.schema import DatabaseSchema, TableSchema


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
        # Extract word tokens from question
        tokens = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', question_lower))

        scored_tables = []
        for tname, tschema in all_tables.items():
            score = 0
            tname_lower = tname.lower()
            
            # Exact or partial table name match
            if tname_lower in question_lower:
                score += 10
            for token in tokens:
                if token in tname_lower or tname_lower in token:
                    score += 5
            
            # Column name matches
            for col in tschema.columns:
                col_name_lower = col.name.lower()
                if col_name_lower in question_lower:
                    score += 4
                for token in tokens:
                    if token in col_name_lower or col_name_lower in token:
                        score += 2

            scored_tables.append((score, tname))

        # Sort by relevance score
        scored_tables.sort(key=lambda x: x[0], reverse=True)
        
        # Pick top scoring tables (minimum score 0, take at least top 3)
        selected_table_names: Set[str] = set()
        for score, tname in scored_tables:
            if score > 0 or len(selected_table_names) < 3:
                selected_table_names.add(tname)
            if len(selected_table_names) >= max_tables - 2:
                break

        # Include 1-hop foreign key adjacent tables to ensure joins can be formed
        adjacent_tables: Set[str] = set()
        for rel in db_schema.relationships:
            if rel.from_table in selected_table_names and rel.to_table in all_tables:
                adjacent_tables.add(rel.to_table)
            elif rel.to_table in selected_table_names and rel.from_table in all_tables:
                adjacent_tables.add(rel.from_table)

        final_table_names = selected_table_names.union(adjacent_tables)
        
        # Cap to max_tables
        final_tables_list = list(final_table_names)[:max_tables]
        
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


def select_relevant_schema(db_schema: DatabaseSchema, question: str, max_tables: int = 8) -> DatabaseSchema:
    """Convenience helper for schema selection."""
    return SchemaSelector.select_relevant_schema(db_schema, question, max_tables=max_tables)
