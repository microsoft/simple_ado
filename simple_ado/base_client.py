#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Base ADO Client."""

import logging

from simple_ado.context import ADOContext
from simple_ado.http_client import ADOHTTPClient


class ADOBaseClient:
    """Base context for ADO API.

    :param context: The context information for the client
    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    log: logging.Logger

    http_client: ADOHTTPClient
    context: ADOContext

    def __init__(
        self, context: ADOContext, http_client: ADOHTTPClient, log: logging.Logger
    ) -> None:
        """Construct a new base client object."""

        self.log = log

        self.context = context
        self.http_client = http_client
