#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO governance API wrapper."""

import enum
import logging
from typing import Any, Dict, List, Optional, Tuple


from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOHTTPException
from simple_ado.http_client import ADOHTTPClient


class ADOGovernanceClient(ADOBaseClient):
    """Wrapper class around the ADO Governance APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    class AlertSeverity(enum.Enum):
        """The potential alert severities."""

        LOW = 0
        MEDIUM = 1
        HIGH = 2
        CRITICAL = 3

        @classmethod
        def _missing_(cls, value):
            if value == "low":
                return cls(0)

            if value == "medium":
                return cls(1)

            if value == "high":
                return cls(2)

            if value == "critical":
                return cls(3)

            return super()._missing_(value)

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("governance"))

    def get_governed_repositories(self, *, project_id: str) -> Dict[str, Any]:
        """Get alert settings for governance for a repository.

        :param str project_id: The ID of the project

        :returns: The settings for the alerts on the repo
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += "/ComponentGovernance/GovernedRepositories"

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def remove_policy(
        self, *, policy_id: str, governed_repository_id: str, project_id: str
    ) -> None:
        """Remove a policy from a repository.

        :param str policy_id: The ID of the policy to remove
        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project

        :raises ADOHTTPException: If removing the policy failed
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += "/ComponentGovernance/GovernedRepositories"
        request_url += f"/{governed_repository_id}/policyreferences"
        request_url += f"/{policy_id}?api-version=5.1-preview.1"

        response = self.http_client.delete(request_url)

        if not response.ok:
            raise ADOHTTPException(
                f"Failed to remove policy {policy_id} from {governed_repository_id}", response
            )

    def _set_alert_settings(
        self, *, alert_settings: Dict[str, Any], governed_repository_id: str, project_id: str
    ) -> None:
        """Set alert settings for governance for a repository.

        :param Dict[str,Any] alert_settings: The settings for the alert on the repo
        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project

        :raises ADOHTTPException: If setting the alert settings failed
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += "/ComponentGovernance/GovernedRepositories"
        request_url += f"/{governed_repository_id}/AlertSettings"
        request_url += "?api-version=5.0-preview.2"

        response = self.http_client.put(request_url, alert_settings)

        if not response.ok:
            raise ADOHTTPException(
                f"Failed to set alert settings on repo {governed_repository_id}", response
            )

    def get_alert_settings(self, *, governed_repository_id: str, project_id: str) -> Dict[str, Any]:
        """Get alert settings for governance for a repository.

        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project

        :returns: The settings for the alerts on the repo
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += "/ComponentGovernance/GovernedRepositories"
        request_url += f"/{governed_repository_id}/AlertSettings"
        request_url += "?api-version=5.0-preview.2"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_show_banner_in_repo_view(self, *, governed_repository_id: str, project_id: str) -> bool:
        """Get whether to show the banner in the repo view or not.

        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project

        :returns: True if the banner is shown in the repo view, False otherwise
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        return current_settings["showRepositoryWarningBanner"]

    def set_show_banner_in_repo_view(
        self, *, show_banner: bool, governed_repository_id: str, project_id: str
    ) -> None:
        """Set whether to show the banner in the repo view or not.

        :param bool show_banner: Set to True to show the banner in the repo view, False to hide it
        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        current_settings["showRepositoryWarningBanner"] = show_banner

        self._set_alert_settings(
            alert_settings=current_settings,
            governed_repository_id=governed_repository_id,
            project_id=project_id,
        )

    def get_minimum_alert_severity(
        self, *, governed_repository_id: str, project_id: str
    ) -> AlertSeverity:
        """Get the minimum severity to alert for.

        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project

        :returns: The minimum alert severity
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        return ADOGovernanceClient.AlertSeverity(current_settings["minimumAlertSeverity"])

    def set_minimum_alert_severity(
        self, *, alert_severity: AlertSeverity, governed_repository_id: str, project_id: str
    ) -> None:
        """Set the minimum severity to alert for.

        :param AlertSeverity alert_severity: The minimum alert serverity to notify about
        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        current_settings["minimumAlertSeverity"] = alert_severity.value

        self._set_alert_settings(
            alert_settings=current_settings,
            governed_repository_id=governed_repository_id,
            project_id=project_id,
        )

    def set_work_item_settings(
        self,
        *,
        create_for_security_alerts: bool,
        create_for_legal_alerts: bool,
        area_path: str,
        work_item_type: str,
        extra_fields: Optional[List[Tuple[str, str]]] = None,
        governed_repository_id: str,
        project_id: str,
    ) -> None:
        """Set whether to show the banner in the repo view or not.

        :param bool create_for_security_alerts: Set to True to create work items for security alerts, False otherwise
        :param bool create_for_legal_alerts: Set to True to create work items for legal alerts, False otherwise
        :param str area_path: The area path to open the tickets under
        :param str work_item_type: The type of work item to create (this must match one in your project)
        :param extra_fields: An optional list of tuples of field IDs and values to set on the created work item
        :param str governed_repository_id: The ID of the governed repository (not necessarily the same as the ADO one)
        :param str project_id: The ID of the project
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        current_settings["workItemSettings"]["areaPath"] = area_path
        current_settings["workItemSettings"][
            "legalAlertWorkItemCreationEnabled"
        ] = create_for_legal_alerts
        current_settings["workItemSettings"][
            "securityAlertWorkItemCreationEnabled"
        ] = create_for_security_alerts
        current_settings["workItemSettings"]["workItemType"] = work_item_type

        if extra_fields:
            current_settings["workItemSettings"]["workItemTemplateRows"] = []
            for field_id, value in extra_fields:
                current_settings["workItemSettings"]["workItemTemplateRows"].append(
                    {"fieldId": field_id, "value": value}
                )

        self._set_alert_settings(
            alert_settings=current_settings,
            governed_repository_id=governed_repository_id,
            project_id=project_id,
        )
