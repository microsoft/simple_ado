"""Token authentication auth class."""

from simple_ado.auth.ado_auth import ADOAuth


class ADOTokenAuth(ADOAuth):
    """Token auth."""

    token: str

    def __init__(self, token: str) -> None:
        self.token = token

    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        return "Bearer " + self.token
