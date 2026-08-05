"""
Custom exceptions.

Design rule (see acceptance criteria "Reliability"): failures must be handled
with clear statuses and must never leak secrets, credentials, or internal
stack traces to the client. Every exception here carries a safe, generic
`public_message` that is what actually gets sent in the HTTP response. The
real detail (if any) is only ever written to the server-side log.
"""


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 400
    public_message: str = "The request could not be processed."

    def __init__(self, public_message: str | None = None, *, log_detail: str | None = None):
        self.public_message = public_message or self.public_message
        self.log_detail = log_detail or self.public_message
        super().__init__(self.public_message)


class NotFoundError(AppError):
    status_code = 404
    public_message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    public_message = "The resource already exists or conflicts with an existing one."


class ValidationAppError(AppError):
    status_code = 422
    public_message = "The request could not be validated."


class AuthenticationError(AppError):
    status_code = 401
    public_message = "Invalid credentials."


class AuthorizationError(AppError):
    status_code = 403
    public_message = "You do not have permission to perform this action."


class TenantMismatchError(AuthorizationError):
    public_message = "You do not have access to this resource."


class DatabaseConnectionError(AppError):
    status_code = 502
    public_message = "Could not connect to the target database."


class SQLValidationError(AppError):
    status_code = 422
    public_message = "The generated SQL failed security validation and was blocked."


class SQLExecutionError(AppError):
    status_code = 502
    public_message = "The query could not be executed against the target database."


class FileProcessingError(AppError):
    status_code = 422
    public_message = "The uploaded file could not be processed."


class LLMProviderError(AppError):
    status_code = 502
    public_message = "The language model provider is currently unavailable."
