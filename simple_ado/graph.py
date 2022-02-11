# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO graph API wrapper."""

import logging
from typing import Any, Iterator, List, Optional


from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOGraphClient(ADOBaseClient):
    """Wrapper class around the ADO Graph APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("graph"))

    def get_scope_descriptors(self, storage_key: str) -> ADOResponse:
        """Get the scope descriptors for a given subject.

        :param storage_key: Storage key (UUID) of the subject (user, group, scope, etc.) to resolve

        :returns: The scope descriptors
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/descriptors/{storage_key}"
        request_url += "/?api-version=6.0-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_storage_key(self, subject_descriptor: str) -> ADOResponse:
        """Get the storage key for a given subject descriptor.

        :param subject_descriptor: Descriptor of the subject to resolve

        :returns: The storage key
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/storagekeys/{subject_descriptor}"
        request_url += "/?api-version=6.0-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def lookup_subjects(self, subject_descriptors: List[str]) -> List[Any]:
        """Lookup the various subject descriptors.

        :param subject_descriptors: Descriptors of the subjects to resolve

        :returns: The lookup keys
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/subjectlookup"
        request_url += "/?api-version=6.0-preview.1"

        data = {"lookupKeys": [{"descriptor": descriptor} for descriptor in subject_descriptors]}

        response = self.http_client.post(request_url, json_data=data)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def list_groups(self, *, scope_descriptor: Optional[str] = None) -> List[Any]:
        """Get the groups in the organization.

        :param scope_descriptor: Specify a non-default scope (collection, project) to search for groups.

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/groups?api-version=5.1-preview.1"

        if scope_descriptor:
            request_url += f"&scopeDescriptor={scope_descriptor}"

        groups: List[Any] = []
        continuation_token = None

        while True:
            if continuation_token:
                url = request_url + f"&continuationToken={continuation_token}"
            else:
                url = request_url

            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            groups += decoded["value"]

            if "X-MS-ContinuationToken" not in response.headers:
                break

            continuation_token = response.headers["X-MS-ContinuationToken"]

        return groups

    def get_group(self, descriptor: str) -> ADOResponse:
        """Get the group

        :param descriptor: The descriptor for the group

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/groups"
        request_url += f"/{descriptor}?api-version=5.1-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_user(self, descriptor: str) -> ADOResponse:
        """Get the user

        :param descriptor: The descriptor for the user

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/users"
        request_url += f"/{descriptor}?api-version=5.1-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def get_users(self) -> ADOResponse:
        """Get the users

        :returns: The ADO response with the data in it
        """

        request_url = f"{self.http_client.graph_endpoint()}/graph/users"
        request_url += "?api-version=6.0-preview.1"
        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)

    def list_users_in_container(self, scope_descriptor: str) -> Iterator[Any]:
        """Get users in the container.

        :param scope_descriptor: Specify a non-default scope (collection, project) to search for users.

        :returns: The ADO response with the data in it
        """

        request_url = (
            f"{self.http_client.graph_endpoint()}/graph/Memberships/"
            + f"{scope_descriptor}?api-version=7.1-preview.1&direction=down"
        )

        continuation_token = None

        while True:
            if continuation_token:
                url = request_url + f"&continuationToken={continuation_token}"
            else:
                url = request_url

            response = self.http_client.get(url)
            decoded = self.http_client.decode_response(response)
            yield from decoded["value"]

            if "X-MS-ContinuationToken" not in response.headers:
                break

            continuation_token = response.headers["X-MS-ContinuationToken"]
