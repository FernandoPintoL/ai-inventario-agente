from typing import Optional, Any


class IntelligentAgentException(Exception):
    """Base exception for the intelligent agent application."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(IntelligentAgentException):
    """Exception raised for database-related errors."""
    pass


class SQLGenerationException(IntelligentAgentException):
    """Exception raised when SQL query generation fails."""
    pass


class LLMException(IntelligentAgentException):
    """Exception raised for Language Model related errors."""
    pass


class ValidationException(IntelligentAgentException):
    """Exception raised for input validation errors."""
    pass


class ConfigurationException(IntelligentAgentException):
    """Exception raised for configuration errors."""
    pass