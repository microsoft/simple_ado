#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO audit API wrapper."""

import datetime
import logging
from typing import Any, Iterator
import urllib.parse

import deserialize

from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient
from simple_ado.models import AuditActionInfo


class ADOAuditClient(ADOBaseClient):
    """Wrapper class around the ADO Audit APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("audit"))

    def get_actions(self, area_name: str | None = None) -> list[AuditActionInfo]:
        """Get the list of audit actions.

        :param area_name: The optional area name to scope down to

        :returns: The ADO response with the data in it
        """

        self.log.debug("Getting audit actions")

        parameters = {"api-version": "6.0-preview.1"}

        if area_name:
            parameters["areaName"] = area_name

        request_url = self.http_client.audit_endpoint() + "/audit/actions?"
        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        raw_actions = self.http_client.extract_value(response_data)
        return deserialize.deserialize(list[AuditActionInfo], raw_actions)

    def query(
        self,
        start_time: datetime.datetime | None = None,
        end_time: datetime.datetime | None = None,
        skip_aggregation: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Query the audit log.

        :param start_time: The earliest point to query (rounds down to the nearest second)
        :param end_time: The latest point to query  (rounds down to the nearest second)
        :param skip_aggregation: Set to False to avoid aggregating events

        :returns: The queried log
        """

        parameters = {"api-version": "6.0-preview.1"}

        if start_time:
            parameters["startTime"] = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if end_time:
            parameters["endTime"] = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if skip_aggregation:
            parameters["skipAggregation"] = str(skip_aggregation).lower()

        request_url = f"{self.http_client.audit_endpoint()}/audit/auditlog?"
        request_url += urllib.parse.urlencode(parameters)

        url = request_url

        while True:
            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            yield from decoded["decoratedAuditLogEntries"]

            if not decoded.get("hasMore"):
                return

            continuation_token = decoded["continuationToken"]
            url = request_url + f"&continuationToken={continuation_token}"
