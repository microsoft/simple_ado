#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Base ADO Client (async)."""

import logging

from simple_ado._async.http_client import ADOAsyncHTTPClient


class ADOAsyncBaseClient:
    """Base client for ADO API.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    log: logging.Logger

    http_client: ADOAsyncHTTPClient

    def __init__(self, http_client: ADOAsyncHTTPClient, log: logging.Logger) -> None:
        """Construct a new base client object."""

        self.log = log
        self.http_client = http_client
