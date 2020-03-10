# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO graph API wrapper."""

import logging


from simple_ado.base_client import ADOBaseClient
from simple_ado.context import ADOContext
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOGraphClient(ADOBaseClient):
    """Wrapper class around the ADO Graph APIs.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(
        self, context: ADOContext, http_client: ADOHTTPClient, log: logging.Logger
    ) -> None:
        super().__init__(context, http_client, log.getChild("graph"))

    def list_groups(self) -> ADOResponse:
        """Get the groups in the organization.

        :returns: The ADO response with the data in it
        """

        # TODO: Add continuation support
        request_url = f"{self.http_client.base_url(is_vssps=True)}/graph/groups?api-version=5.1-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)
