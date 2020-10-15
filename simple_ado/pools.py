#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO pools API wrapper."""

import enum
import logging
from typing import Any, Dict, Optional
import urllib.parse


from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class TaskAgentPoolActionFilter(enum.Enum):
    """Represents an agent pool action filter."""

    manage = "manage"
    none = "none"
    use = "use"


class ADOPoolsClient(ADOBaseClient):
    """Wrapper class around the undocumented ADO pools APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("pools"))

    def get_pools(
        self,
        *,
        pool_name: Optional[str] = None,
        action_filter: Optional[TaskAgentPoolActionFilter] = None,
    ) -> ADOResponse:
        """Gets the agent details.

        :param Optional[str] pool_name: The name of the pool to match on
        :param Optional[TaskAgentPoolActionFilter] action_filter: Set to filter on the type of pools

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(is_default_collection=False)
        request_url += f"/distributedtask/pools?"

        parameters = {"api-version": "5.1"}

        if pool_name:
            parameters["poolName"] = pool_name

        if action_filter:
            parameters["actionFilter"] = action_filter.value

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_agents(
        self,
        *,
        pool_id: int,
        agent_name: Optional[str] = None,
        include_capabilities: bool = True,
        include_assigned_request: bool = True,
        include_last_completed_request: bool = True,
    ) -> ADOResponse:
        """Gets the agents details.

        :param int pool_id: The ID of the pool the agents are in
        :param Optional[str] agent_name: The name of the agent to match on
        :param bool include_capabilities: Set to False to not include capabilities
        :param bool include_assigned_request: Set to False to not include the current assigned request
        :param bool include_last_completed_request: Set to False to not include the last completed request

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(is_default_collection=False)
        request_url += f"/distributedtask/pools/{pool_id}/agents?"

        parameters = {
            "includeCapabilities": include_capabilities,
            "includeAssignedRequest": include_assigned_request,
            "includeLastCompletedRequest": include_last_completed_request,
            "api-version": "5.1",
        }

        if agent_name:
            parameters["agentName"] = agent_name

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_agent(self, *, pool_id: int, agent_id: int) -> ADOResponse:
        """Gets the agent details.

        :param int pool_id: The ID of the pool the agent is in
        :param int agent_id: The ID of the agent to get

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(is_default_collection=False)
        request_url += f"/distributedtask/pools/{pool_id}/agents/{agent_id}?api-version=5.1"

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def update_agent(
        self, *, pool_id: int, agent_id: int, agent_data: Dict[str, Any]
    ) -> ADOResponse:
        """Adds required reviewers when opening PRs against a given branch.

        :param int pool_id: The ID of the pool the agent is in
        :param int agent_id: The ID of the agent to disable
        :param Dict[str,Any] agent_data: The data to set on the agent

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(is_default_collection=False)
        request_url += f"/distributedtask/pools/{pool_id}/agents/{agent_id}?api-version=5.1"

        response = self.http_client.patch(request_url, json_data=agent_data)
        return self.http_client.decode_response(response)

    def set_agent_state(self, *, pool_id: int, agent_id: int, enabled: bool) -> ADOResponse:
        """Set the enabled/disabled state of an agent.

        :param int pool_id: The ID of the pool the agent is in
        :param int agent_id: The ID of the agent to disable
        :param bool enabled: Set to True to enable an agent, False to disable it

        :returns: The ADO response with the data in it
        """

        agent_details = self.get_agent(pool_id=pool_id, agent_id=agent_id)
        agent_details["enabled"] = enabled
        return self.update_agent(pool_id=pool_id, agent_id=agent_id, agent_data=agent_details)

    def update_agent_capabilities(
        self, *, pool_id: int, agent_id: int, capabilities: Dict[str, str]
    ) -> ADOResponse:
        """Set the enabled/disabled state of an agent.

        :param int pool_id: The ID of the pool the agent is in
        :param int agent_id: The ID of the agent to disable
        :param Dict[str,str] capabilities: The new capabilities to set

        :returns: The ADO response with the data in it
        """

        request_url = self.http_client.api_endpoint(is_default_collection=False)
        request_url += (
            f"/distributedtask/pools/{pool_id}/agents/{agent_id}/usercapabilities?api-version=5.1"
        )

        response = self.http_client.put(request_url, json_data=capabilities)
        return self.http_client.decode_response(response)
