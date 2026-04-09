#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO user API wrapper (async)."""

import logging

from simple_ado._async.base_client import ADOAsyncBaseClient
from simple_ado._async.http_client import ADOAsyncHTTPClient


class ADOAsyncUserClient(ADOAsyncBaseClient):
    """Wrapper class around the ADO user APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOAsyncHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("user"))
