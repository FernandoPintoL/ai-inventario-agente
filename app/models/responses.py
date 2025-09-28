from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class QueryResponse(BaseModel):
    """Response model for successful queries."""

    answer: str = Field(..., description="Natural language answer to the query")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    raw_data: Optional[List[Dict[str, Any]]] = Field(None, description="Raw database results")
    execution_time: Optional[float] = Field(None, description="Query execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
    table_info: Optional[str] = Field(None, description="Database schema information if requested")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Hay 150 productos en el almacén principal.",
                "sql_query": "SELECT COUNT(*) FROM productos WHERE almacen_id = 1",
                "raw_data": [{"count": 150}],
                "execution_time": 0.045,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Failed to generate SQL query",
                "error_type": "SQLGenerationException",
                "details": {"original_query": "invalid query"},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }