# THIS FILE IS AUTO-GENERATED FROM simple_ado/_async/auth/ado_azid_auth.py. DO NOT EDIT.

"""Azure Identity authentication auth class."""

import time

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
from simple_ado.auth.ado_auth import ADOAuth


class ADOAzIDAuth(ADOAuth):
    """Azure Identity auth."""

    access_token: AccessToken | None
    _credential: DefaultAzureCredential

    def __init__(self) -> None:
        self.access_token = None
        self._credential = DefaultAzureCredential()

    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        # The get_token parameter specifies the Azure DevOps resource and requests a token with
        # default permissions for API access.
        if self.access_token is None or self.access_token.expires_on <= time.time() + 60:
            self.access_token = self._credential.get_token(
                "499b84ac-1321-427f-aa17-267ca6975798/.default"
            )

        return "Bearer " + self.access_token.token

    def close(self) -> None:
        """Close the underlying credential."""
        self._credential.close()
