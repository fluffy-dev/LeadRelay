from src.exceptions import AppError

class OperatorNotFound(AppError):
    """Raised when an operator is not found."""
    pass

class SourceNotFound(AppError):
    """Raised when a source is not found."""
    pass

class NoAvailableOperators(AppError):
    """Raised when no suitable operator can be found for a lead."""
    pass