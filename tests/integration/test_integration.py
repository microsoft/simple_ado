#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Integration tests for the package - requires real ADO access."""

# pylint: disable=line-too-long

from collections import defaultdict
import datetime
import os
from typing import Any

import pytest
import yaml

import simple_ado


@pytest.fixture(name="client")
def fixture_client(integration_client: simple_ado.ADOClient) -> simple_ado.ADOClient:
    """Return the integration client."""
    return integration_client


@pytest.fixture(name="project_id")
def fixture_project_id(integration_project_id: str) -> str:
    """Return the integration project ID."""
    return integration_project_id


@pytest.fixture(name="repository_id")
def fixture_repository_id(integration_repo_id: str) -> str:
    """Return the integration repository ID."""
    return integration_repo_id


@pytest.mark.integration
def test_access(client: simple_ado.ADOClient) -> None:
    """Test access."""
    client.verify_access()


@pytest.mark.integration
@pytest.mark.destructive
def test_get_blobs(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test get blobs."""
    client.git.get_blobs(
        blob_ids=[
            "7351cd0c84377c067602e97645e9c91100c38a6e",
            "bcb7f5028bf4f26a005d315a4863670e3125c262",
        ],
        output_path=os.path.expanduser("~/Downloads/blobs.zip"),
        project_id=project_id,
        repository_id=repository_id,
    )


@pytest.mark.integration
def test_get_blob(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test get blob."""
    diff = client.git.get_blob(
        blob_id="7351cd0c84377c067602e97645e9c91100c38a6e",
        blob_format=simple_ado.git.ADOGitClient.BlobFormat.TEXT,
        project_id=project_id,
        repository_id=repository_id,
    )
    assert diff is not None


@pytest.mark.integration
def test_git_diff(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test git diff."""
    all_prs = client.list_all_pull_requests(
        project_id=project_id,
        repository_id=repository_id,
    )
    details = next(all_prs)
    diff = client.git.diff_between_commits(
        base_commit=details["lastMergeTargetCommit"]["commitId"],
        target_commit=details["lastMergeSourceCommit"]["commitId"],
        project_id=project_id,
        repository_id=repository_id,
    )
    assert len(diff["changes"]) > 0


@pytest.mark.integration
@pytest.mark.destructive
def test_properties(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test get properties."""
    all_prs = client.list_all_pull_requests(
        project_id=project_id,
        repository_id=repository_id,
    )
    latest_pr = next(all_prs)
    pr_id = latest_pr["pullRequestId"]

    base_properties = client.pull_request(
        pr_id,
        project_id=project_id,
        repository_id=repository_id,
    ).get_properties()
    base_count = len(base_properties)

    new_properties = client.pull_request(
        pr_id,
        project_id=project_id,
        repository_id=repository_id,
    ).add_property("Hello", "World")
    assert len(new_properties) == base_count + 1

    after_deletion = client.pull_request(
        pr_id,
        project_id=project_id,
        repository_id=repository_id,
    ).delete_property("Hello")
    assert len(after_deletion) == base_count


@pytest.mark.integration
def test_list_repos(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test list repos."""
    repos = client.git.all_repositories(project_id=project_id)
    assert len(repos) > 0, "Failed to find any repos"

    repo = client.git.get_repository(project_id=project_id, repository_id=repos[0]["id"])
    assert repo is not None, "Failed to get repo"

    default_branch = repo["defaultBranch"].replace("refs/heads/", "")

    stats = client.git.get_stats_for_branch(
        project_id=project_id,
        repository_id=repo["id"],
        branch_name=default_branch,
    )
    assert stats is not None


@pytest.mark.integration
def test_list_refs(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test list refs."""
    refs = client.git.get_refs(
        project_id=project_id,
        repository_id=repository_id,
    )
    assert len(refs) > 0, "Failed to find any refs"


@pytest.mark.integration
def test_get_commit(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test get commit."""
    refs = client.git.get_refs(
        project_id=project_id,
        repository_id=repository_id,
    )
    ref = refs[0]
    commit_id = ref["objectId"]
    commit = client.git.get_commit(
        commit_id=commit_id,
        project_id=project_id,
        repository_id=repository_id,
    )
    assert commit is not None


@pytest.mark.integration
def test_get_pull_requests(
    client: simple_ado.ADOClient, project_id: str, repository_id: str
) -> None:
    """Test get pull requests."""
    refs = client.list_all_pull_requests(
        project_id=project_id,
        repository_id=repository_id,
    )
    assert len(list(refs)) > 0


@pytest.mark.integration
def test_get_pools(client: simple_ado.ADOClient) -> None:
    """Test get pools."""
    response = client.pools.get_pools()
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.destructive
def test_capabilities(client: simple_ado.ADOClient) -> None:
    """Test setting capabilities."""
    pool = client.pools.get_pools(action_filter=simple_ado.pools.TaskAgentPoolActionFilter.MANAGE)[
        0
    ]
    agent = client.pools.get_agents(pool_id=pool["id"])[0]
    capabilities = agent["userCapabilities"]
    capabilities["hello"] = "world"
    client.pools.update_agent_capabilities(
        pool_id=pool["id"], agent_id=agent["id"], capabilities=capabilities
    )


@pytest.mark.integration
def test_get_pr_statuses(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test get properties."""
    all_prs = client.list_all_pull_requests(
        project_id=project_id,
        repository_id=repository_id,
    )
    latest_pr = next(all_prs)
    pr_id = latest_pr["pullRequestId"]
    statuses = client.pull_request(
        pr_id,
        project_id=project_id,
        repository_id=repository_id,
    ).get_statuses()
    assert statuses is not None


@pytest.mark.integration
def test_audit_actions(client: simple_ado.ADOClient) -> None:
    """Test get audit actions"""
    actions = client.audit.get_actions()
    assert actions is not None


@pytest.mark.integration
def test_audit_query(client: simple_ado.ADOClient) -> None:
    """Test query audit entries."""
    for entry in client.audit.query():
        assert entry is not None
        break


@pytest.mark.integration
def test_get_branch_policies(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test getting governance repos."""
    policy_map: dict[str, list[Any]] = defaultdict(list)

    for policy in client.security.get_policies(project_id):
        for scope in policy["settings"]["scope"]:
            policy_map[scope["repositoryId"]].append(policy)

    for repo in client.git.all_repositories(project_id):
        policies = policy_map.get(repo["id"])
        assert policies is not None


@pytest.mark.integration
def test_get_pipelines(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test getting pipelines."""
    pipeline = None

    for basic_pipeline in client.pipelines.get_pipelines(project_id=project_id, top=10):
        pipeline = client.pipelines.get_pipeline(
            project_id=project_id, pipeline_id=basic_pipeline["id"]
        )
        break

    assert pipeline is not None

    raw_yaml = client.pipelines.preview(project_id=project_id, pipeline_id=12778)
    assert raw_yaml is not None
    data = yaml.safe_load(raw_yaml)
    assert data is not None

    run = None

    for base_run in client.pipelines.get_top_ten_thousand_runs(
        project_id=project_id, pipeline_id=pipeline["id"]
    ):
        run = client.pipelines.get_run(
            project_id=project_id,
            pipeline_id=pipeline["id"],
            run_id=base_run["id"],
        )
        break

    assert run is not None


@pytest.mark.integration
def test_get_groups_users(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test getting groups/users."""
    project_descriptor = client.graph.get_scope_descriptors(project_id)

    for group in client.graph.list_groups(scope_descriptor=project_descriptor["value"]):
        details = client.graph.get_group(group["descriptor"])
        assert details is not None
        for member in client.graph.list_users_in_container(group["descriptor"]):
            assert member is not None
            break
        break


@pytest.mark.integration
def test_get_endpoints(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test getting endpoints groups/users."""
    endpoints = client.endpoints.get_endpoints(project_id=project_id, endpoint_type="azurerm")

    for endpoint in endpoints:
        for item in client.endpoints.get_usage_history(
            project_id=project_id,
            endpoint_id=endpoint["id"],
            top=75,
        ):
            assert item is not None

    assert endpoints is not None


@pytest.mark.integration
def test_get_leases(client: simple_ado.ADOClient, project_id: str) -> None:
    """Remove a pipeline."""
    for pipeline in client.pipelines.get_pipelines(top=3, project_id=project_id):
        pipeline_id = pipeline["id"]

        for build in client.builds.get_builds(project_id=project_id, definitions=[pipeline_id]):
            leases = client.builds.get_leases(project_id=project_id, build_id=build["id"])

            assert leases is not None
            break


@pytest.mark.integration
def test_get_definitions(client: simple_ado.ADOClient, project_id: str) -> None:
    """Get definitions."""
    for definition in client.builds.get_definitions(project_id=project_id):
        definition_id = definition["id"]

        full_definition = client.builds.get_definition(
            project_id=project_id, definition_id=definition_id
        )

        assert full_definition is not None


@pytest.mark.integration
def test_list_prs(client: simple_ado.ADOClient, project_id: str, repository_id: str) -> None:
    """Test list PRs diff."""
    count = 0
    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=28)
    for pull_request in client.list_all_pull_requests(
        project_id=project_id,
        repository_id=repository_id,
        pr_status=simple_ado.pull_requests.ADOPullRequestStatus.COMPLETED,
    ):
        closed_date = datetime.datetime.strptime(
            pull_request["closedDate"][:-2], "%Y-%m-%dT%H:%M:%S.%f"
        )
        if closed_date < one_month_ago:
            break
        count += 1
    assert count > 0


@pytest.mark.integration
def test_list_workitems(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test list PRs diff."""

    found_workitems = client.workitems.execute_query(
        project_id=project_id,
        query_string="Select [System.Id] From WorkItems where [System.ChangedDate] >= @Today - 1",
    )
    wids = [item["id"] for item in found_workitems["workItems"][:500]]
    count = 0
    for _ in client.workitems.ilist(wids, project_id=project_id):
        count += 1
    assert count == len(wids)


@pytest.mark.integration
@pytest.mark.destructive
def test_get_and_update_workitem(client: simple_ado.ADOClient, project_id: str) -> None:
    """Test get work item."""
    workitem_info = client.workitems.get(identifier="2704094", project_id=project_id)
    workitem = simple_ado.ADOWorkItem(workitem_info, client.workitems, project_id, client.log)

    assert workitem_info["fields"]["System.Title"] == workitem["System.Title"]

    try:
        workitem["System.Title"] = "Updated Title"
        new_workitem_info = client.workitems.get(identifier="2704094", project_id=project_id)
        assert new_workitem_info["fields"]["System.Title"] == "Updated Title"

    finally:
        # Return to original
        workitem["System.Title"] = workitem_info["fields"]["System.Title"]
