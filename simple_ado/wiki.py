# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO Wiki API wrapper."""

import logging

from simple_ado.exceptions import ADOException
from simple_ado.base_client import ADOBaseClient
from simple_ado.http_client import ADOHTTPClient, ADOResponse


class ADOWikiClient(ADOBaseClient):
    """Wrapper class around the ADO Wiki APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("wiki"))

    def get_page_version(self, page_id: str, wiki_id: str, project_id: str) -> ADOResponse:
        """Get's the current version of a wiki page. This returns a required parameter for updating a wiki page.

        https://docs.microsoft.com/en-us/rest/api/azure/devops/wiki/pages/get%20page%20by%20id?view=azure-devops-rest-6.1

        :param page_id: Wiki page ID
        :param wiki_id: Wiki ID or Wiki name
        :param project_id: The ID of the project

        :returns: The ADO response with the data in it

        :raises ADOException: If we fail to fetch the page version.
        """

        self.log.debug(f"Get wiki page: {page_id}")
        request_url = (
            self.http_client.api_endpoint(is_default_collection=False, project_id=project_id)
            + f"/wiki/wikis/{wiki_id}/pages/{page_id}?api-version=6.1-preview.1"
        )
        response = self.http_client.get(request_url)
        self.http_client.validate_response(response)
        etag = response.headers.get("ETag")
        if not etag:
            raise ADOException("No ETag returned for wiki page.")
        return etag

    def update_page(
        self,
        page_id: str,
        wiki_id: str,
        project_id: str,
        content: str,
        current_version_etag: str,
    ) -> ADOResponse:
        """Update a the contents of a wiki page.

        https://docs.microsoft.com/en-us/rest/api/azure/devops/wiki/pages/update?view=azure-devops-rest-6.1

        :param page_id: Wiki page ID
        :param wiki_id: Wiki ID or Wiki name
        :param project_id: The ID of the project
        :param content: Content of the wiki page.
        :param current_version_etag: The ETag of the current wiki page to verify the update.

        :returns: The ADO response with the data in it
        """

        self.log.debug(f"Updating wiki page: {page_id}")
        request_url = (
            self.http_client.api_endpoint(is_default_collection=False, project_id=project_id)
            + f"/wiki/wikis/{wiki_id}/pages/{page_id}?api-version=6.1-preview.1"
        )
        response = self.http_client.patch(
            request_url,
            json_data={
                "content": content,
            },
            additional_headers={
                "Content-Type": "application/json",
                "If-Match": current_version_etag,
            },
        )
        return self.http_client.decode_response(response)
