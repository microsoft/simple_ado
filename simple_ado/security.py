#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO security API wrapper."""

import enum
import json
import logging
from typing import ClassVar, Dict, List, Optional
import urllib.parse


from simple_ado.base_client import ADOBaseClient
from simple_ado.exceptions import ADOException
from simple_ado.http_client import ADOHTTPClient, ADOResponse
from simple_ado.types import TeamFoundationId


class ADOBranchPermission(enum.IntEnum):
    """Possible types of git branch permissions."""

    ADMINISTER: int = 2 ** 0
    READ: int = 2 ** 1
    CONTRIBUTE: int = 2 ** 2
    FORCE_PUSH: int = 2 ** 3
    CREATE_BRANCH: int = 2 ** 4
    CREATE_TAG: int = 2 ** 5
    MANAGE_NOTES: int = 2 ** 6
    BYPASS_PUSH_POLICIES: int = 2 ** 7
    CREATE_REPOSITORY: int = 2 ** 8
    DELETE_REPOSITORY: int = 2 ** 9
    RENAME_REPOSITORY: int = 2 ** 10
    EDIT_POLICIES: int = 2 ** 11
    REMOVE_OTHERS_LOCKS: int = 2 ** 12
    MANAGE_PERMISSIONS: int = 2 ** 13
    CONTRIBUTE_TO_PULL_REQUESTS: int = 2 ** 14
    BYPASS_PULL_REQUEST_POLICIES: int = 2 ** 15


class ADOBranchPermissionLevel(enum.IntEnum):
    """Possible values of git branch permissions."""

    NOT_SET: int = 0
    ALLOW: int = 1
    DENY: int = 2


class ADOBranchPolicy(enum.Enum):
    """Possible types of git branch protections."""

    APPROVAL_COUNT: str = "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd"
    BUILD: str = "0609b952-1397-4640-95ec-e00a01b2c241"
    CASE_ENFORCEMENT: str = "7ed39669-655c-494e-b4a0-a08b4da0fcce"
    MAXIMUM_BLOB_SIZE: str = "2e26e725-8201-4edd-8bf5-978563c34a80"
    MERGE_STRATEGY: str = "fa4e907d-c16b-4a4c-9dfa-4916e5d171ab"
    REQUIRED_REVIEWERS: str = "fd2167ab-b0be-447a-8ec8-39368250530e"
    STATUS_CHECK: str = "cbdc66da-9728-4af8-aada-9a5a32e4a226"
    WORK_ITEM: str = "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e"


class ADOPolicyApplicability(enum.Enum):
    """Different types of policy applicability."""

    APPLY_BY_DEFAULT = None
    CONDITIONAL = 1


class ADOSecurityClient(ADOBaseClient):
    """Wrapper class around the undocumented ADO Security APIs.

    :param http_client: The HTTP client to use for the client
    :param log: The logger to use
    """

    GIT_PERMISSIONS_NAMESPACE: ClassVar[str] = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"

    def __init__(self, http_client: ADOHTTPClient, log: logging.Logger) -> None:
        super().__init__(http_client, log.getChild("security"))

    def get_policies(self, project_id: str) -> ADOResponse:
        """Gets the existing policies.

        :param project_id: The identifier for the project

        :returns: The ADO response with the data in it
        """
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )
        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def delete_policy(self, project_id: str, policy_id: int) -> None:
        """Delete a policy.

        :param project_id: The identifier for the project
        :param policy_id: The ID of the policy to delete
        """
        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + f"/policy/Configurations/{policy_id}?api-version=6.0"
        )
        response = self.http_client.delete(request_url)
        self.http_client.validate_response(response)

    # pylint: disable=too-many-locals
    def add_branch_status_check_policy(
        self,
        *,
        branch: str,
        is_blocking: bool = True,
        is_enabled: bool = True,
        required_status_author_id: Optional[str] = None,
        default_display_name: Optional[str] = None,
        invalidate_on_source_update: bool = True,
        filename_filter: Optional[List[str]] = None,
        applicability: ADOPolicyApplicability = ADOPolicyApplicability.APPLY_BY_DEFAULT,
        status_name: str,
        status_genre: str,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Adds a new status check policy for a given branch.

        :param str branch: The git branch to set the policy for
        :param bool is_blocking: Whether the status blocks PR completion or not.
        :param bool is_enabled: Whether the status is enabled or not.
        :param Optional[str] required_status_author_id: The ID of a required author (None if anyone)
        :param Optional[str] default_display_name: The default display name for the policy
        :param bool invalidate_on_source_update: Set to True to invalid the status when an update to
                                                 the PR happens, False otherwise
        :param Optional[List[str]] filename_filter: A list of file name filters this policy should
                                                    only apply to
        :param ADOPolicyApplicability applicability: Set to apply always or just if the status is posted
        :param str status_name: The name of the status
        :param str status_genre: The genre of the status
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )

        settings = {
            "authorId": required_status_author_id,
            "defaultDisplayName": default_display_name,
            "invalidateOnSourceUpdate": invalidate_on_source_update,
            "policyApplicability": applicability.value,
            "statusName": status_name,
            "statusGenre": status_genre,
            "scope": [
                {
                    "repositoryId": repository_id,
                    "refName": f"refs/heads/{branch}",
                    "matchKind": "Exact",
                }
            ],
        }

        if filename_filter:
            settings["filenamePatterns"] = filename_filter

        body = {
            "type": {"id": ADOBranchPolicy.STATUS_CHECK.value},
            "revision": 1,
            "isDeleted": False,
            "isBlocking": is_blocking,
            "isEnabled": is_enabled,
            "settings": settings,
        }

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    # pylint: enable=too-many-locals

    def add_branch_build_policy(
        self,
        *,
        branch: str,
        build_definition_id: int,
        build_expiration: Optional[int] = None,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Adds a new build policy for a given branch.

        :param str branch: The git branch to set the build policy for
        :param int build_definition_id: The build definition to use when creating the build policy
        :param int build_expiration: How long in minutes before the build expires. Set to None for
                                     immediately on changes to source branch.
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )

        body = {
            "type": {"id": ADOBranchPolicy.BUILD.value},
            "revision": 1,
            "isDeleted": False,
            "isBlocking": True,
            "isEnabled": True,
            "settings": {
                "buildDefinitionId": build_definition_id,
                "displayName": None,
                "queueOnSourceUpdateOnly": build_expiration is not None,
                "manualQueueOnly": False,
                "validDuration": build_expiration if build_expiration is not None else 0,
                "scope": [
                    {
                        "refName": f"refs/heads/{branch}",
                        "matchKind": "Exact",
                        "repositoryId": repository_id,
                    }
                ],
            },
        }

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def add_branch_required_reviewers_policy(
        self,
        *,
        branch: str,
        identities: List[str],
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Adds required reviewers when opening PRs against a given branch.

        :param str branch: The git branch to set required reviewers for
        :param List[str] identities: A list of identities to become required
                                     reviewers (should be team foundation IDs)
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )

        body = {
            "type": {"id": ADOBranchPolicy.REQUIRED_REVIEWERS.value},
            "revision": 1,
            "isDeleted": False,
            "isBlocking": True,
            "isEnabled": True,
            "settings": {
                "requiredReviewerIds": identities,
                "filenamePatterns": [],
                "addedFilesOnly": False,
                "ignoreIfSourceIsInScope": False,
                "message": None,
                "scope": [
                    {
                        "refName": f"refs/heads/{branch}",
                        "matchKind": "Exact",
                        "repositoryId": repository_id,
                    }
                ],
            },
        }

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def set_branch_approval_count_policy(
        self,
        *,
        branch: str,
        minimum_approver_count: int,
        creator_vote_counts: bool = False,
        reset_on_source_push: bool = False,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Set minimum number of reviewers for a branch.

        :param str branch: The git branch to set minimum number of reviewers on
        :param int minimum_approver_count: The minimum number of approvals required
        :param bool creator_vote_counts: Allow users to approve their own changes
        :param bool reset_on_source_push: Reset reviewer votes when there are new changes
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )

        body = {
            "type": {"id": ADOBranchPolicy.APPROVAL_COUNT.value},
            "revision": 2,
            "isDeleted": False,
            "isBlocking": True,
            "isEnabled": True,
            "settings": {
                "minimumApproverCount": minimum_approver_count,
                "creatorVoteCounts": creator_vote_counts,
                "resetOnSourcePush": reset_on_source_push,
                "scope": [
                    {
                        "refName": f"refs/heads/{branch}",
                        "matchKind": "exact",
                        "repositoryId": repository_id,
                    }
                ],
            },
        }

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def set_branch_work_item_policy(
        self,
        *,
        branch: str,
        required: bool = True,
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Set the work item policy for a branch.

        :param str branch: The git branch to set the work item policy on
        :param bool required: Whether or not linked work items should be mandatory
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        request_url = (
            self.http_client.api_endpoint(project_id=project_id)
            + "/policy/Configurations?api-version=5.0"
        )

        body = {
            "type": {"id": ADOBranchPolicy.WORK_ITEM.value},
            "revision": 2,
            "isDeleted": False,
            "isBlocking": required,
            "isEnabled": True,
            "settings": {
                "scope": [
                    {
                        "refName": f"refs/heads/{branch}",
                        "matchKind": "Exact",
                        "repositoryId": repository_id,
                    }
                ]
            },
        }

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def set_branch_permissions(
        self,
        *,
        branch: str,
        identity: TeamFoundationId,
        permissions: Dict[ADOBranchPermission, ADOBranchPermissionLevel],
        project_id: str,
        repository_id: str,
    ) -> ADOResponse:
        """Set permissions for an identity on a branch.

        :param str branch: The git branch to set permissions on
        :param TeamFoundationId identity: The identity to set permissions for (should be team foundation ID)
        :param Dict[ADOBranchPermission,ADOBranchPermissionLevel] permissions: A dictionary of permissions to set
        :param str project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The ADO response with the data in it
        """

        descriptor_info = self._get_descriptor_info(
            branch=branch,
            team_foundation_id=identity,
            project_id=project_id,
            repository_id=repository_id,
        )

        request_url = self.http_client.api_endpoint(is_internal=True, project_id=project_id)
        request_url += "/_security/ManagePermissions?__v=5"

        updates = []
        for permission, level in permissions.items():
            updates.append(
                {
                    "PermissionId": level,
                    "PermissionBit": permission,
                    "NamespaceId": ADOSecurityClient.GIT_PERMISSIONS_NAMESPACE,
                    "Token": self.generate_updates_token(
                        branch_name=branch, project_id=project_id, repository_id=repository_id
                    ),
                }
            )

        package = {
            "IsRemovingIdentity": False,
            "TeamFoundationId": identity,
            "DescriptorIdentityType": descriptor_info["type"],
            "DescriptorIdentifier": descriptor_info["id"],
            "PermissionSetId": ADOSecurityClient.GIT_PERMISSIONS_NAMESPACE,
            "PermissionSetToken": self._generate_permission_set_token(
                branch=branch, project_id=project_id, repository_id=repository_id
            ),
            "RefreshIdentities": False,
            "Updates": updates,
            "TokenDisplayName": None,
        }

        body = {"updatePackage": json.dumps(package)}

        response = self.http_client.post(request_url, json_data=body)
        return self.http_client.decode_response(response)

    def _get_descriptor_info(
        self,
        *,
        branch: str,
        team_foundation_id: TeamFoundationId,
        project_id: str,
        repository_id: str,
    ) -> Dict[str, str]:
        """Fetch the descriptor identity information for a given identity.

        :param str branch: The git branch of interest
        :param TeamFoundationId team_foundation_id: the unique Team Foundation GUID for the identity
        :param project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The raw descriptor info

        :raises ADOException: If we can't determine the descriptor info from the response
        """

        request_url = self.http_client.api_endpoint(is_internal=True, project_id=project_id)
        request_url += "/_security/DisplayPermissions?"

        parameters = {
            "tfid": team_foundation_id,
            "permissionSetId": ADOSecurityClient.GIT_PERMISSIONS_NAMESPACE,
            "permissionSetToken": self._generate_permission_set_token(
                branch=branch, project_id=project_id, repository_id=repository_id
            ),
            "__v": "5",
        }

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)

        try:
            descriptor_info = {
                "type": response_data["descriptorIdentityType"],
                "id": response_data["descriptorIdentifier"],
            }
        except Exception as ex:
            raise ADOException(
                "Could not determine descriptor info for team_foundation_id: "
                + str(team_foundation_id)
            ) from ex

        return descriptor_info

    def _generate_permission_set_token(
        self,
        branch: str,
        project_id: str,
        repository_id: str,
    ) -> str:
        """Generate the token required for reading identity details and writing permissions.

        :param str branch: The git branch of interest
        :param str project_id: The ID for the project
        :param str repository_id: The ID for the repository

        :returns: The permission token
        """
        _ = self
        encoded_branch = branch.replace("/", "^")
        return f"repoV2/{project_id}/{repository_id}/refs^heads^{encoded_branch}/"

    def generate_updates_token(
        self,
        *,
        project_id: str,
        repository_id: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> str:
        """Generate the token required for updating permissions.

        A project ID must always be set. Repository ID and branch name are
        optional, but if a branch name is set, then a repository ID must also be
        set.

        :param project_id: The ID for the project
        :param repository_id: The ID for the repository
        :param branch_name: The git branch of interest

        :returns: The update token
        """

        _ = self

        token = f"repoV2/{project_id}/"

        if not repository_id:
            return token

        token += f"{repository_id}/"

        if not branch_name:
            return token

        # Encode each node in the branch to hex
        encoded_branch_nodes = [node.encode("utf-16le").hex() for node in branch_name.split("/")]

        encoded_branch = "/".join(encoded_branch_nodes)

        return token + f"refs/heads/{encoded_branch}/"

    def query_namespaces(
        self, *, namespace_id: str, local_only: Optional[bool] = None
    ) -> ADOResponse:
        """Query a namespace

        :param namespace_id: The identifier for the namespace
        :param local_only: Specify whether to check local namespaces only or not

        :returns: The ADO response with the data in it
        """
        request_url = (
            self.http_client.api_endpoint()
            + f"/securitynamespaces/{namespace_id}?api-version=7.1-preview.1"
        )

        if local_only is not None:
            request_url += f"&localOnly={local_only}".lower()

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def query_access_control_lists(
        self,
        *,
        namespace_id: str,
        descriptors: Optional[List[str]] = None,
        token: Optional[str] = None,
    ) -> ADOResponse:
        """Query a namespace

        :param namespace_id: The identifier for the namespace
        :param descriptors: An optional of list of descriptors to filter down to those.
        :param token: An optional token to filter down to

        :returns: The ADO response with the data in it
        """

        if descriptors is None:
            descriptors = []

        descriptors = [
            "Microsoft.TeamFoundation.Identity;" + descriptor
            if not descriptor.startswith("Microsoft.TeamFoundation.Identity;")
            else descriptor
            for descriptor in descriptors
        ]

        request_url = (
            self.http_client.api_endpoint()
            + f"/accesscontrollists/{namespace_id}?api-version=7.1-preview.1"
        )

        if len(descriptors) > 0:
            request_url += "&descriptors=" + ",".join(descriptors)

        if token:
            request_url += f"&token={token}"

        response = self.http_client.get(request_url)
        response_data = self.http_client.decode_response(response)
        return self.http_client.extract_value(response_data)

    def get_permissions(
        self,
        *,
        branch: str,
        team_foundation_id: TeamFoundationId,
        project_id: str,
        repository_id: str,
    ) -> Dict[str, str]:
        """Get the permissions for a branch

        :param str branch: The name of the branch to get the permissions for
        :param TeamFoundationId team_foundation_id: the unique Team Foundation GUID for the identity
        :param project_id: The identifier for the project
        :param str repository_id: The ID for the repository

        :returns: The raw descriptor info

        :raises ADOException: If we can't determine the descriptor info from the response
        """

        request_url = self.http_client.api_endpoint(is_internal=True, project_id=project_id)
        request_url += "/_security/DisplayPermissions?"

        parameters = {
            "tfid": team_foundation_id,
            "permissionSetId": ADOSecurityClient.GIT_PERMISSIONS_NAMESPACE,
            "permissionSetToken": self._generate_permission_set_token(
                branch=branch, project_id=project_id, repository_id=repository_id
            ),
            "__v": "5",
        }

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_client.get(request_url)
        return self.http_client.decode_response(response)
