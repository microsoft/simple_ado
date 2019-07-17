#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Context object."""


class ADOContext:
    """Context information for the ADO Client.

    :param str username: The username of the bot account
    :param str repository_id: The ID of the repository
    :param str status_context: The name of the status context to use for build status notifications
    """

    username: str
    repository_id: str
    status_context: str

    def __init__(self, *, username: str, repository_id: str, status_context: str) -> None:
        """Construct a new client object."""

        self.username = username
        self.repository_id = repository_id
        self.status_context = status_context
