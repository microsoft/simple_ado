# THIS FILE IS AUTO-GENERATED FROM simple_ado/_async/auth/ado_auth.py. DO NOT EDIT.

"""Base auth class."""

import abc


class ADOAuth(abc.ABC):
    """Base class for authentication."""

    @abc.abstractmethod
    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""
        raise NotImplementedError()

    def close(self) -> None:
        """Close any resources held by this auth instance.

        Subclasses that hold closeable resources (e.g. credential objects)
        should override this method. The default implementation is a no-op.
        """
