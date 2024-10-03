from typing import Any, Dict, Optional

from httpx import Response
from pydantic import ValidationError as PydanticValidationError


class JavelinClientError(Exception):
    """
    Base exception class for JavelinClient errors.

    Attributes
    ----------
    message : str
        The error message associated with the JavelinClient error.
    response_data : Optional[dict]
        The response data associated with the JavelinClient error.

    Parameters
    ----------
    message : str
        The error message to be set for the exception.
    response : Optional[Response]
        The httpx.Response object associated with the error, by default None.
    """

    def __init__(self, message: str, response: Optional[Response] = None) -> None:
        super().__init__(message)
        self.message = message
        self.response_data = self._extract_response_data(response)

    def _extract_response_data(
        self, response: Optional[Response]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract response data from a httpx.Response object.

        Parameters
        ----------
        response : Optional[Response]
            The httpx.Response object to extract data from.

        Returns
        -------
        Optional[Dict[str, Any]]
            A dictionary containing details about the response, or None
            if response is None.
        """
        if response is None:
            return {"status_code": None, "response_text": "No response data available"}
        else:
            # Extract and customize the response data specifically for validation errors
            return {
                "status_code": response.status_code,
                "response_text": response.text
                or "The provided data did not pass validation checks.",
            }

    def __str__(self):
        return f"{self.message}: {self.response_data}"


class GatewayNotFoundError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Gateway not found"
    ) -> None:
        super().__init__(message=message, response=response)


class GatewayAlreadyExistsError(JavelinClientError):
    def __init__(
        self,
        response: Optional[Response] = None,
        message: str = "Gateway already exists",
    ) -> None:
        super().__init__(message=message, response=response)


class RouteNotFoundError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Route not found"
    ) -> None:
        super().__init__(message=message, response=response)


class RouteAlreadyExistsError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Route already exists"
    ) -> None:
        super().__init__(message=message, response=response)


class ProviderNotFoundError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Provider not found"
    ) -> None:
        super().__init__(message=message, response=response)


class ProviderAlreadyExistsError(JavelinClientError):
    def __init__(
        self,
        response: Optional[Response] = None,
        message: str = "Provider already exists",
    ) -> None:
        super().__init__(message=message, response=response)


class TemplateNotFoundError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Template not found"
    ) -> None:
        super().__init__(message=message, response=response)


class TemplateAlreadyExistsError(JavelinClientError):
    def __init__(
        self,
        response: Optional[Response] = None,
        message: str = "Template already exists",
    ) -> None:
        super().__init__(message=message, response=response)


class SecretNotFoundError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Secret not found"
    ) -> None:
        super().__init__(message=message, response=response)


class SecretAlreadyExistsError(JavelinClientError):
    def __init__(
        self,
        response: Optional[Response] = None,
        message: str = "Secret already exists",
    ) -> None:
        super().__init__(message=message, response=response)


class NetworkError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Connection error"
    ) -> None:
        super().__init__(message=message, response=response)


class BadRequest(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Bad Request"
    ) -> None:
        super().__init__(message=message, response=response)


class RateLimitExceededError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Rate limit exceeded"
    ) -> None:
        super().__init__(message=message, response=response)


class InternalServerError(JavelinClientError):
    def __init__(
        self,
        response: Optional[Response] = None,
        message: str = "Internal server error",
    ) -> None:
        super().__init__(message=message, response=response)


class MethodNotAllowedError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Method not allowed"
    ) -> None:
        super().__init__(message=message, response=response)


class UnauthorizedError(JavelinClientError):
    def __init__(
        self, response: Optional[Response] = None, message: str = "Access denied"
    ) -> None:
        super().__init__(message=message, response=response)

    # Override the __str__ method to only return the message
    def __str__(self):
        return self.message


class ValidationError(JavelinClientError):
    def __init__(
        self, error: PydanticValidationError, message: str = "Validation error occurred"
    ) -> None:
        super().__init__(message=message)
        self.error = error

    def __str__(self):
        return f"{self.message}: {self.error}"
