"""
Custom exceptions for the application.
"""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class DuplicateError(AppException):
    """Duplicate resource exception."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InsufficientStockError(AppException):
    """Insufficient stock exception."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class BusinessRuleError(AppException):
    """Business rule violation exception."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)
