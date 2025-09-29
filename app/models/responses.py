from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class TableColumn(BaseModel):
    """Column information for structured table data."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type (string, number, boolean, date)")
    nullable: bool = Field(default=True, description="Whether column allows null values")


class StructuredTableData(BaseModel):
    """Structured table data for external systems."""

    columns: List[TableColumn] = Field(..., description="Column definitions")
    rows: List[List[Any]] = Field(..., description="Data rows as arrays")
    total_rows: int = Field(..., description="Total number of rows")

    model_config = {
        "json_schema_extra": {
            "example": {
                "columns": [
                    {"name": "producto_id", "type": "number", "nullable": False},
                    {"name": "nombre", "type": "string", "nullable": False},
                    {"name": "stock", "type": "number", "nullable": True}
                ],
                "rows": [
                    [1, "Producto A", 25],
                    [2, "Producto B", 0],
                    [3, "Producto C", 15]
                ],
                "total_rows": 3
            }
        }
    }


class QueryResponse(BaseModel):
    """Response model for successful queries."""

    answer: str = Field(..., description="Natural language answer to the query")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    raw_data: Optional[List[Dict[str, Any]]] = Field(None, description="Raw database results")
    structured_data: Optional[StructuredTableData] = Field(None, description="Structured table data for reports")
    execution_time: Optional[float] = Field(None, description="Query execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
    table_info: Optional[str] = Field(None, description="Database schema information if requested")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Encontré 3 productos con stock bajo en el almacén principal.",
                "sql_query": "SELECT id, nombre, stock FROM productos WHERE stock < 10 AND almacen_id = 1",
                "raw_data": [
                    {"id": 1, "nombre": "Producto A", "stock": 5},
                    {"id": 2, "nombre": "Producto B", "stock": 2},
                    {"id": 3, "nombre": "Producto C", "stock": 8}
                ],
                "structured_data": {
                    "columns": [
                        {"name": "id", "type": "number", "nullable": False},
                        {"name": "nombre", "type": "string", "nullable": False},
                        {"name": "stock", "type": "number", "nullable": True}
                    ],
                    "rows": [
                        [1, "Producto A", 5],
                        [2, "Producto B", 2],
                        [3, "Producto C", 8]
                    ],
                    "total_rows": 3
                },
                "execution_time":
                    0.045,
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