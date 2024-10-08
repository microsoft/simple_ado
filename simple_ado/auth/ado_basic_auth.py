"""Basic authentication auth class."""

import base64
import functools
from simple_ado.auth.ado_auth import ADOAuth


class ADOBasicAuth(ADOAuth):
    """Username/password auth. Also supports PATs."""

    username: str
    password: str

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    @functools.lru_cache(maxsize=1)
    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        username_password_bytes = (self.username + ":" + self.password).encode("utf-8")
        return "Basic " + base64.b64encode(username_password_bytes).decode("utf-8")
