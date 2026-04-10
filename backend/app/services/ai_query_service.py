"""
AI Query Service.
Interface for natural language to structured query conversion.

This service is designed to be AI-ready. Currently implements
rule-based parsing with clear extension points for LLM integration.
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.schemas.analytics import (
    AIQueryResponse,
    StructuredQuery,
    QueryType,
)


class AIQueryService:
    """
    Service for converting natural language queries to structured queries.

    Current implementation uses rule-based pattern matching.
    Designed for easy LLM integration in the future.

    Extension points:
    - Add LLM client in _parse_with_llm()
    - Integrate with vector database for query embeddings
    - Add query caching for common questions
    """

    # Pattern mappings for rule-based parsing
    ENTITY_MAPPINGS = {
        "product": "products",
        "products": "products",
        "item": "products",
        "items": "products",
        "inventory": "inventory",
        "stock": "inventory",
        "sale": "sales",
        "sales": "sales",
        "order": "sales",
        "orders": "sales",
        "customer": "customers",
        "reorder": "reorder_rules",
    }

    AGGREGATION_PATTERNS = {
        "total": "sum",
        "sum": "sum",
        "average": "avg",
        "avg": "avg",
        "mean": "avg",
        "count": "count",
        "how many": "count",
        "min": "min",
        "minimum": "min",
        "max": "max",
        "maximum": "max",
    }

    def __init__(self):
        pass

    def parse_query(self, query: str, context: Optional[str] = None) -> AIQueryResponse:
        """
        Parse a natural language query into a structured query.

        Args:
            query: Natural language query string
            context: Optional additional context

        Returns:
            AIQueryResponse with structured query and explanation
        """
        query_lower = query.lower().strip()

        # Determine query type
        query_type = self._detect_query_type(query_lower)

        # Detect target entity
        target_entity = self._detect_entity(query_lower)

        # Extract filters
        filters = self._extract_filters(query_lower)

        # Extract aggregations
        aggregations = self._extract_aggregations(query_lower)

        # Extract ordering
        order_by = self._extract_ordering(query_lower)

        # Extract limit
        limit = self._extract_limit(query_lower)

        # Extract time range
        time_range = self._extract_time_range(query_lower)

        # Build structured query
        structured_query = StructuredQuery(
            query_type=query_type,
            target_entity=target_entity,
            filters=filters if filters else None,
            aggregations=aggregations if aggregations else None,
            order_by=order_by,
            limit=limit,
            time_range=time_range,
            raw_query=query,
        )

        # Generate explanation
        explanation = self._generate_explanation(structured_query)

        # Calculate confidence (higher for rule-based matches)
        confidence = self._calculate_confidence(query_lower, structured_query)

        return AIQueryResponse(
            original_query=query,
            structured_query=structured_query,
            explanation=explanation,
            confidence=confidence,
        )

    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query based on keywords."""

        # Check for aggregation keywords
        for keyword in self.AGGREGATION_PATTERNS.keys():
            if keyword in query:
                return QueryType.AGGREGATE

        # Check for comparison keywords
        comparison_words = ["compare", "vs", "versus", "difference", "between"]
        if any(word in query for word in comparison_words):
            return QueryType.COMPARISON

        # Check for trend keywords
        trend_words = ["trend", "over time", "history", "change", "growth"]
        if any(word in query for word in trend_words):
            return QueryType.TREND

        # Check for filter keywords
        filter_words = ["where", "with", "that", "which", "in", "from"]
        if any(word in query for word in filter_words):
            return QueryType.FILTER

        # Default to LIST
        return QueryType.LIST

    def _detect_entity(self, query: str) -> str:
        """Detect the target entity from the query."""
        for keyword, entity in self.ENTITY_MAPPINGS.items():
            if keyword in query:
                return entity

        # Default to products
        return "products"

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filter conditions from the query."""
        filters = {}

        # Category filter
        category_match = re.search(r"category\s+(?:is\s+)?([a-zA-Z\s]+?)(?:\s|$|,|and)", query)
        if category_match:
            filters["category"] = category_match.group(1).strip()

        # Status filter
        if "active" in query:
            filters["is_active"] = True
        if "inactive" in query:
            filters["is_active"] = False

        # Low stock filter
        if "low stock" in query or "low inventory" in query:
            filters["low_stock"] = True

        # Price filters
        price_min_match = re.search(r"price\s+(?:above|>=?)\s*\$?(\d+)", query)
        if price_min_match:
            filters["min_price"] = float(price_min_match.group(1))

        price_max_match = re.search(r"price\s+(?:below|<=?)\s*\$?(\d+)", query)
        if price_max_match:
            filters["max_price"] = float(price_max_match.group(1))

        return filters

    def _extract_aggregations(self, query: str) -> List[str]:
        """Extract aggregation functions from the query."""
        aggregations = []

        for keyword, agg_func in self.AGGREGATION_PATTERNS.items():
            if keyword in query and agg_func not in aggregations:
                aggregations.append(agg_func)

        return aggregations

    def _extract_ordering(self, query: str) -> Optional[str]:
        """Extract ordering from the query."""
        if "top" in query or "best" in query or "highest" in query:
            return "desc"
        if "bottom" in query or "worst" in query or "lowest" in query:
            return "asc"
        if "newest" in query or "recent" in query:
            return "created_at desc"
        if "oldest" in query:
            return "created_at asc"

        return None

    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit from the query."""
        # Match "top N" or "first N" patterns
        limit_match = re.search(r"(?:top|first|last|show\s+)\s*(\d+)", query)
        if limit_match:
            return int(limit_match.group(1))

        # Match "top 10" style
        top_match = re.search(r"top\s+(\d+)", query)
        if top_match:
            return int(top_match.group(1))

        return None

    def _extract_time_range(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract time range from the query."""
        now = datetime.utcnow()

        if "today" in query:
            return {
                "from": now.replace(hour=0, minute=0, second=0, microsecond=0),
                "to": now,
            }

        if "yesterday" in query:
            yesterday = now - timedelta(days=1)
            return {
                "from": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                "to": yesterday.replace(hour=23, minute=59, second=59),
            }

        # Week patterns
        week_match = re.search(r"(\d+)\s*weeks?", query)
        if week_match:
            weeks = int(week_match.group(1))
            return {
                "from": now - timedelta(weeks=weeks),
                "to": now,
                "period": f"{weeks} weeks",
            }

        # Month patterns
        month_match = re.search(r"(\d+)\s*months?", query)
        if month_match:
            months = int(month_match.group(1))
            return {
                "from": now - timedelta(days=months * 30),
                "to": now,
                "period": f"{months} months",
            }

        # Day patterns
        day_match = re.search(r"(\d+)\s*days?", query)
        if day_match:
            days = int(day_match.group(1))
            return {
                "from": now - timedelta(days=days),
                "to": now,
                "period": f"{days} days",
            }

        return None

    def _generate_explanation(self, structured_query: StructuredQuery) -> str:
        """Generate a human-readable explanation of the parsed query."""
        parts = []

        # Entity
        parts.append(f"Querying {structured_query.target_entity}")

        # Query type
        if structured_query.query_type == QueryType.AGGREGATE:
            parts.append(f"with aggregations: {', '.join(structured_query.aggregations or [])}")
        elif structured_query.query_type == QueryType.FILTER:
            parts.append("with filters applied")

        # Filters
        if structured_query.filters:
            filter_parts = []
            for key, value in structured_query.filters.items():
                filter_parts.append(f"{key}={value}")
            parts.append(f"filters: {', '.join(filter_parts)}")

        # Ordering
        if structured_query.order_by:
            parts.append(f"ordered by {structured_query.order_by}")

        # Limit
        if structured_query.limit:
            parts.append(f"limited to {structured_query.limit} results")

        # Time range
        if structured_query.time_range:
            period = structured_query.time_range.get("period", "custom period")
            parts.append(f"time range: {period}")

        return " | ".join(parts)

    def _calculate_confidence(self, query: str, structured_query: StructuredQuery) -> float:
        """Calculate confidence score for the parsed query."""
        confidence = 0.5  # Base confidence

        # Increase confidence for recognized entities
        if structured_query.target_entity in self.ENTITY_MAPPINGS.values():
            confidence += 0.2

        # Increase confidence for recognized query types
        if structured_query.query_type != QueryType.UNKNOWN:
            confidence += 0.1

        # Increase confidence for queries with filters or aggregations
        if structured_query.filters or structured_query.aggregations:
            confidence += 0.1

        # Cap at 0.95 (rule-based is never 100% certain)
        return min(0.95, confidence)

    def execute_query(self, structured_query: StructuredQuery) -> Dict[str, Any]:
        """
        Execute a structured query and return results.

        Note: This is a mock implementation. In production, this would
        execute against the actual database.

        Args:
            structured_query: Parsed structured query

        Returns:
            Query results
        """
        # This is where LLM integration would happen
        # For now, return a mock response
        return {
            "status": "mock_execution",
            "query": structured_query.model_dump(),
            "message": "Query parsed successfully. Execute against database for results.",
        }

    async def parse_with_llm(self, query: str, context: Optional[str] = None) -> AIQueryResponse:
        """
        Parse query using an LLM (future implementation).

        This method is designed for LLM integration. When integrating:
        1. Add LLM client (Anthropic, OpenAI, etc.)
        2. Define prompt template for query parsing
        3. Parse LLM response into StructuredQuery
        4. Add error handling for malformed responses

        Args:
            query: Natural language query
            context: Additional context

        Returns:
            AIQueryResponse with structured query
        """
        # TODO: Implement LLM integration
        # Example integration points:
        # - Anthropic Claude API
        # - OpenAI GPT
        # - Local LLM (Ollama, vLLM)

        # For now, fall back to rule-based parsing
        return self.parse_query(query, context)
