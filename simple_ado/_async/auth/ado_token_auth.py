"""Token authentication async auth class."""

from simple_ado._async.auth.ado_auth import ADOAsyncAuth


class ADOAsyncTokenAuth(ADOAsyncAuth):
    """Token auth."""

    token: str

    def __init__(self, token: str) -> None:
        self.token = token

    async def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        return "Bearer " + self.token
