"""Base async auth class."""

import abc


class ADOAsyncAuth(abc.ABC):
    """Base class for async authentication."""

    @abc.abstractmethod
    async def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""
        raise NotImplementedError()

    async def close(self) -> None:
        """Close any resources held by this auth instance.

        Subclasses that hold closeable resources (e.g. credential objects)
        should override this method. The default implementation is a no-op.
        """
