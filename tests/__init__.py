# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Base test cases."""

import os
from typing import Any, Dict, List, Optional

import toml


class TestDetails:
    """Holds the test details."""

    repository_id: str
    token: str
    username: str
    tenant: str
    project_id: str

    def __init__(self) -> None:
        self.token = os.environ["SIMPLE_ADO_BASE_TOKEN"]
        self.username = os.environ["SIMPLE_ADO_USERNAME"]
        self.tenant = os.environ["SIMPLE_ADO_TENANT"]
        self.repository_id = os.environ["SIMPLE_ADO_REPO_ID"]
        self.project_id = os.environ["SIMPLE_ADO_PROJECT_ID"]
