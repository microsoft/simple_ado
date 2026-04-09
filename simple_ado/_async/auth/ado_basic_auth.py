"""Basic authentication async auth class."""

import base64
from simple_ado._async.auth.ado_auth import ADOAsyncAuth


class ADOAsyncBasicAuth(ADOAsyncAuth):
    """Username/password auth. Also supports PATs."""

    username: str
    password: str
    _cached_header: str | None

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self._cached_header = None

    async def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        if self._cached_header is None:
            username_password_bytes = (self.username + ":" + self.password).encode("utf-8")
            self._cached_header = "Basic " + base64.b64encode(username_password_bytes).decode(
                "utf-8"
            )

        return self._cached_header
