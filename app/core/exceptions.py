class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(AppException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, status_code=401)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message=message, status_code=422)
