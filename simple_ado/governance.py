#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO governance API wrapper."""

import enum
import logging
from typing import Any
import urllib.parse


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

    def get_governed_repositories(self, *, project_id: str) -> dict[str, Any]:
        """Get all governed repositories for the project

        :param project_id: The ID of the project

        :returns: The governed repositories
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += "/ComponentGovernance/GovernedRepositories?api-version=6.1-preview.1"

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_governed_repository(
        self, *, governed_repository_id: str | int, project_id: str
    ) -> dict[str, Any]:
        """Get a particular governed repository.

        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

        :returns: The governed repository details
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += f"/ComponentGovernance/GovernedRepositories/{governed_repository_id}?api-version=6.1-preview.1"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def delete_governed_repository(
        self, *, governed_repository_id: str | int, project_id: str
    ) -> None:
        """Delete a governed repository.

        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += f"/ComponentGovernance/GovernedRepositories/{governed_repository_id}?api-version=6.1-preview.1"

        response = self.http_client.delete(request_url)
        self.http_client.validate_response(response)

    def remove_policy(
        self,
        *,
        policy_id: str,
        governed_repository_id: str | int,
        project_id: str,
    ) -> None:
        """Remove a policy from a repository.

        :param policy_id: The ID of the policy to remove
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

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
                f"Failed to remove policy {policy_id} from {governed_repository_id}",
                response,
            )

    def _set_alert_settings(
        self,
        *,
        alert_settings: dict[str, Any],
        governed_repository_id: str | int,
        project_id: str,
    ) -> None:
        """Set alert settings for governance for a repository.

        :param alert_settings: The settings for the alert on the repo
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

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
                f"Failed to set alert settings on repo {governed_repository_id}",
                response,
            )

    def get_alert_settings(
        self, *, governed_repository_id: str | int, project_id: str
    ) -> dict[str, Any]:
        """Get alert settings for governance for a repository.

        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

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

    def get_show_banner_in_repo_view(
        self, *, governed_repository_id: str | int, project_id: str
    ) -> bool:
        """Get whether to show the banner in the repo view or not.

        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

        :returns: True if the banner is shown in the repo view, False otherwise
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        return current_settings["showRepositoryWarningBanner"]

    def set_show_banner_in_repo_view(
        self,
        *,
        show_banner: bool,
        governed_repository_id: str | int,
        project_id: str,
    ) -> None:
        """Set whether to show the banner in the repo view or not.

        :param show_banner: Set to True to show the banner in the repo view, False to hide it
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project
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
        self, *, governed_repository_id: str | int, project_id: str
    ) -> AlertSeverity:
        """Get the minimum severity to alert for.

        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

        :returns: The minimum alert severity
        """

        current_settings = self.get_alert_settings(
            governed_repository_id=governed_repository_id, project_id=project_id
        )

        return ADOGovernanceClient.AlertSeverity(current_settings["minimumAlertSeverity"])

    def set_minimum_alert_severity(
        self,
        *,
        alert_severity: AlertSeverity,
        governed_repository_id: str | int,
        project_id: str,
    ) -> None:
        """Set the minimum severity to alert for.

        :param alert_severity: The minimum alert serverity to notify about
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project
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
        extra_fields: list[tuple[str, str]] | None = None,
        governed_repository_id: str | int,
        project_id: str,
    ) -> None:
        """Set whether to show the banner in the repo view or not.

        :param create_for_security_alerts: Set to True to create work items for security alerts, False otherwise
        :param create_for_legal_alerts: Set to True to create work items for legal alerts, False otherwise
        :param area_path: The area path to open the tickets under
        :param work_item_type: The type of work item to create (this must match one in your project)
        :param extra_fields: An optional list of tuples of field IDs and values to set on the created work item
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project
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

    def get_branches(
        self,
        *,
        tracked_only: bool = True,
        governed_repository_id: str | int,
        project_id: str,
    ) -> dict[str, Any]:
        """Get the branches for the goverened repository.

        Note: Due to lack of documentation, the pagination for this API is
        unclear and therefore this call can only return the top 99,999 results.
        If there are any more than this, the call will return the top 99,999 and
        exit.

        :param tracked_only: Set to True if only tracked branches should be returned (default), False otherwise
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

        :returns: The settings for the alerts on the repo
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += (
            f"/ComponentGovernance/GovernedRepositories/{governed_repository_id}/Branches?"
        )

        parameters = {"top": 99999, "isTracked": tracked_only}

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_alerts(
        self,
        *,
        branch_name: str,
        include_history: bool = False,
        include_development_dependencies: bool = True,
        governed_repository_id: str | int,
        project_id: str,
    ) -> dict[str, Any]:
        """Get the alerts on a given branch.

        :param branch_name: The branch to get the alerts for
        :param include_history: It isn't clear what this parameter does. Defaults to False
        :param include_development_dependencies: Set to True to include alerts on development
                                                      dependencies, False otherwise (defaults to True)
        :param governed_repository_id: The repository governance ID
        :param project_id: The ID of the project

        :returns: The settings for the alerts on the repo
        """

        request_url = self.http_client.api_endpoint(
            is_default_collection=False, subdomain="governance", project_id=project_id
        )
        request_url += (
            f"/ComponentGovernance/GovernedRepositories/{governed_repository_id}"
            + f"/Branches/{branch_name}/Alerts?"
        )

        parameters = {
            "includeHistory": include_history,
            "includeDevelopmentDependencies": include_development_dependencies,
        }

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)
