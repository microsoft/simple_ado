# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Base test cases."""

import os
from typing import Any, Dict, List, Optional

import toml


class TestDetails:
    """Holds the test details."""

    repository_id: str
    token_identifier: str
    token: str
    username: str
    tenant: str
    project_id: str

    def __init__(
            self,
            *,
            repository_id: str,
            token_identifier: str,
            username: str,
            tenant: str,
            project_id: str
    ) -> None:
        self.repository_id = repository_id
        self.token_identifier = token_identifier
        self.username = username
        self.tenant = tenant
        self.project_id = project_id

        token = os.environ.get(token_identifier)

        if token:
            self.token = token
        else:
            raise Exception(f"No token was available for identifier: {token_identifier}")


def load_test_details() -> TestDetails:
    """Load the test details from disk."""

    module_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(module_path, "test_config.toml")

    with open(config_path, 'r') as config_file:
        config = toml.load(config_file)

    repository_id = config["repository_id"]
    token_identifier = config["token_identifier"]
    username = config["username"]
    tenant = config["tenant"]
    project_id = config["project_id"]

    return TestDetails(
        repository_id=repository_id,
        token_identifier=token_identifier,
        username=username,
        tenant=tenant,
        project_id=project_id
    )
