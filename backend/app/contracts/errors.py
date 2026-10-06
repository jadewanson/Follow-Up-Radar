from __future__ import annotations


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigurationError(DomainError):
    code = "configuration_error"


class AuthenticationError(DomainError):
    code = "authentication_error"


class AuthorizationError(DomainError):
    code = "authorization_error"


class ValidationError(DomainError):
    code = "validation_error"


class NotFoundError(DomainError):
    code = "not_found"


class StateTransitionError(DomainError):
    code = "invalid_state_transition"
