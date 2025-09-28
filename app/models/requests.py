from pydantic import BaseModel, Field, field_validator
from typing import Optional


class HumanQueryRequest(BaseModel):
    """Request model for human language queries."""

    human_query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language query to be converted to SQL"
    )

    include_table_info: Optional[bool] = Field(
        default=False,
        description="Whether to include database schema information in response"
    )

    limit_results: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )

    @field_validator('human_query')
    @classmethod
    def validate_query(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")

        # Basic security checks - prevent certain dangerous SQL keywords
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        query_lower = v.lower()

        for keyword in dangerous_keywords:
            if keyword in query_lower:
                raise ValueError(f"Query contains potentially dangerous keyword: {keyword}")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "human_query": "¿Cuántos productos hay en el almacén principal?",
                "include_table_info": False,
                "limit_results": 100
            }
        }
    }