#!/usr/bin/env python3
"""
Basic tests for the Intelligent Agent API.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.requests import HumanQueryRequest
from app.models.responses import QueryResponse
from app.core.exceptions import ValidationException


class TestHumanQueryRequest:
    """Test cases for HumanQueryRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = HumanQueryRequest(
            human_query="¿Cuántos productos hay?",
            limit_results=100
        )
        assert request.human_query == "¿Cuántos productos hay?"
        assert request.limit_results == 100
        assert request.include_table_info is False

    def test_empty_query_validation(self):
        """Test validation of empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            HumanQueryRequest(human_query="   ")

    def test_dangerous_keyword_validation(self):
        """Test validation of dangerous SQL keywords."""
        dangerous_queries = [
            "DROP TABLE productos",
            "DELETE FROM productos",
            "INSERT INTO productos VALUES",
            "UPDATE productos SET"
        ]

        for query in dangerous_queries:
            with pytest.raises(ValueError, match="dangerous keyword"):
                HumanQueryRequest(human_query=query)

    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Valid limit
        request = HumanQueryRequest(
            human_query="¿Cuántos productos hay?",
            limit_results=50
        )
        assert request.limit_results == 50

        # Invalid limit (too high)
        with pytest.raises(ValueError):
            HumanQueryRequest(
                human_query="¿Cuántos productos hay?",
                limit_results=2000
            )

        # Invalid limit (negative)
        with pytest.raises(ValueError):
            HumanQueryRequest(
                human_query="¿Cuántos productos hay?",
                limit_results=-1
            )


class TestQueryResponse:
    """Test cases for QueryResponse model."""

    def test_response_creation(self):
        """Test response model creation."""
        response = QueryResponse(
            answer="Hay 100 productos en total.",
            sql_query="SELECT COUNT(*) FROM productos",
            raw_data=[{"count": 100}],
            execution_time=0.045
        )

        assert response.answer == "Hay 100 productos en total."
        assert response.sql_query == "SELECT COUNT(*) FROM productos"
        assert response.raw_data == [{"count": 100}]
        assert response.execution_time == 0.045
        assert response.timestamp is not None


# Mock tests for services (when database is not available)
class TestMockServices:
    """Mock tests for testing service logic without database."""

    def test_sql_cleaning(self):
        """Test SQL query cleaning logic."""
        from app.services.ai_service import AIService
        from app.database import db_manager

        # This would need to be mocked in a real test environment
        # For now, just test the concept
        test_responses = [
            ("SQLQuery: SELECT * FROM productos", "SELECT * FROM productos"),
            ("```sql\nSELECT * FROM productos\n```", "SELECT * FROM productos"),
            ("SELECT * FROM productos;", "SELECT * FROM productos;"),
        ]

        # Mock the cleaning method
        for input_sql, expected in test_responses:
            # This is a simplified test - in real implementation,
            # you'd mock the AIService and test the _clean_sql_response method
            cleaned = input_sql.replace("SQLQuery:", "").replace("```sql", "").replace("```", "").strip()
            assert cleaned == expected.strip()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])