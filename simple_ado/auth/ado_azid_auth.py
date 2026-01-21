"""Azure Identity authentication auth class."""

from azure.identity import DefaultAzureCredential
from simple_ado.auth.ado_auth import ADOAuth


class ADOAzIDAuth(ADOAuth):
    """Azure Identity auth."""

    def get_authorization_header(self) -> str:
        """Get the header value.

        :return: The header value."""

        # The get_token parameter specifies the Azure DevOps resource and requests a token with
        # default permissions for API access.
        return (
            "Bearer "
            + DefaultAzureCredential()
            .get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")
            .token
        )
