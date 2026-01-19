"""Base auth class."""

import abc


class ADOAuth(abc.ABC):
    """Base class for authentication."""

    @abc.abstractmethod
    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""
        raise NotImplementedError()
