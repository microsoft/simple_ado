#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO user API wrapper."""

import logging

from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient


class ADOUserClient(ADOBaseClient):
    """Wrapper class around the ADO user APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("user"))
