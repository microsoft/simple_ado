#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Tests for the package."""

# pylint: disable=line-too-long,too-many-public-methods

from collections import defaultdict
import os
import sys
import unittest

import yaml

from . import TestDetails

sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "..")))
import simple_ado  # pylint: disable=wrong-import-order


class LibraryTests(unittest.TestCase):
    """Basic tests."""

    def setUp(self) -> None:
        """Set up method."""
        self.test_config = TestDetails()
        self.client = simple_ado.ADOClient(
            tenant=self.test_config.tenant,
            credentials=(self.test_config.username, self.test_config.token),
        )

    def test_access(self):
        """Test access."""
        self.client.verify_access()

    def test_get_blobs(self):
        """Test get blobs."""
        self.client.git.get_blobs(
            blob_ids=[
                "7351cd0c84377c067602e97645e9c91100c38a6e",
                "bcb7f5028bf4f26a005d315a4863670e3125c262",
            ],
            output_path=os.path.expanduser("~/Downloads/blobs.zip"),
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        )

    def test_get_blob(self):
        """Test get blob."""
        diff = self.client.git.get_blob(
            blob_id="7351cd0c84377c067602e97645e9c91100c38a6e",
            blob_format=simple_ado.git.ADOGitClient.BlobFormat.TEXT,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        )
        print(diff)

    def test_git_diff(self):
        """Test git diff."""
        all_prs = self.client.list_all_pull_requests(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        details = all_prs[0]
        diff = self.client.git.diff_between_commits(
            base_commit=details["lastMergeTargetCommit"]["commitId"],
            target_commit=details["lastMergeSourceCommit"]["commitId"],
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        )
        assert len(diff["changes"]) > 0

    def test_properties(self):
        """Test get properties."""
        all_prs = self.client.list_all_pull_requests(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        latest_pr = all_prs[0]
        pr_id = latest_pr["pullRequestId"]
        pr_id = 441259
        base_properties = self.client.pull_request(
            pr_id,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        ).get_properties()
        base_count = len(base_properties)
        new_properties = self.client.pull_request(
            pr_id,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        ).add_property("Hello", "World")
        self.assertEqual(base_count + 1, len(new_properties))
        after_deletion = self.client.pull_request(
            pr_id,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        ).delete_property("Hello")
        self.assertEqual(len(after_deletion), base_count)
        print("Done")

    def test_list_repos(self):
        """Test list repos."""
        repos = self.client.git.all_repositories(project_id=self.test_config.project_id)
        self.assertTrue(len(repos) > 0, "Failed to find any repos")
        repo = self.client.git.get_repository(
            project_id=self.test_config.project_id, repository_id=repos[0]["id"]
        )
        self.assertIsNotNone(repo, "Failed to get repo")
        default_branch = repo["defaultBranch"].replace("refs/heads/", "")

        stats = self.client.git.get_stats_for_branch(
            project_id=self.test_config.project_id,
            repository_id=repo["id"],
            branch_name=default_branch,
        )
        self.assertIsNotNone(stats)

    def test_list_refs(self):
        """Test list refs."""
        refs = self.client.git.get_refs(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        self.assertTrue(len(refs) > 0, "Failed to find any refs")

    def test_get_commit(self):
        """Test get commit."""
        refs = self.client.git.get_refs(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        ref = refs[0]
        commit_id = ref["objectId"]
        commit = self.client.git.get_commit(
            commit_id=commit_id,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        )
        self.assertIsNotNone(commit)

    # TODO: We can't test this until we can also create branches
    # def test_delete_branch(self):
    #    """Test delete branch."""
    #    response = self.client.git.delete_branch("refs/heads/?", "?")
    #    for value in response:
    #        self.assertTrue(value["success"])

    def test_get_pull_requests(self):
        """Test get pull requests."""
        refs = self.client.list_all_pull_requests(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        self.assertTrue(len(refs) > 0)

    def test_get_pools(self):
        """Test get pools."""
        response = self.client.pools.get_pools()
        self.assertGreater(len(response), 0)

    def test_capabilities(self):
        """Test setting capabilities."""
        pool = self.client.pools.get_pools(
            action_filter=simple_ado.pools.TaskAgentPoolActionFilter.MANAGE
        )[0]
        agent = self.client.pools.get_agents(pool_id=pool["id"])[0]
        capabilities = agent["userCapabilities"]
        capabilities["hello"] = "world"
        self.client.pools.update_agent_capabilities(
            pool_id=pool["id"], agent_id=agent["id"], capabilities=capabilities
        )

    def test_get_pr_statuses(self):
        """Test get properties."""
        all_prs = self.client.list_all_pull_requests(
            project_id=self.test_config.project_id, repository_id=self.test_config.repository_id
        )
        latest_pr = all_prs[0]
        pr_id = latest_pr["pullRequestId"]
        statuses = self.client.pull_request(
            pr_id,
            project_id=self.test_config.project_id,
            repository_id=self.test_config.repository_id,
        ).get_statuses()
        print(statuses)

    def test_audit_actions(self):
        """Test get audit actions"""
        actions = self.client.audit.get_actions()
        print(actions)

    def test_audit_query(self):
        """Test query audit entries."""
        for entry in self.client.audit.query():
            print(entry)
            break

    def test_goverance(self):
        """Test getting governance repos."""

        governed_repos_list = self.client.governance.get_governed_repositories(
            project_id=self.test_config.project_id,
        )

        repo = self.client.governance.get_governed_repository(
            governed_repository_id=governed_repos_list[0]["id"],
            project_id=self.test_config.project_id,
        )

        del repo["policies"]
        del repo["projectReference"]

        self.assertEqual(repo, governed_repos_list[0])

        branches = self.client.governance.get_branches(
            tracked_only=True,
            governed_repository_id=repo["id"],
            project_id=self.test_config.project_id,
        )

        self.assertTrue(len(branches) > 0)

        shows_banner = self.client.governance.get_show_banner_in_repo_view(
            governed_repository_id=repo["id"],
            project_id=self.test_config.project_id,
        )

        self.assertIsNotNone(shows_banner)

        alerts = self.client.governance.get_alerts(
            branch_name=branches[0]["name"],
            governed_repository_id=repo["id"],
            project_id=self.test_config.project_id,
        )

        self.assertIsNotNone(alerts)

    def test_get_branch_policies(self):
        """Test getting governance repos."""

        policy_map = defaultdict(list)

        for policy in self.client.security.get_policies(self.test_config.project_id):
            for scope in policy["settings"]["scope"]:
                policy_map[scope["repositoryId"]].append(policy)

        for repo in self.client.git.all_repositories(self.test_config.project_id):
            policies = policy_map.get(repo["id"])

            assert policies is not None

    def test_get_pipelines(self):
        """Test getting pipelines."""

        pipeline = None

        for basic_pipeline in self.client.pipelines.get_pipelines(
            project_id=self.test_config.project_id, top=10
        ):
            pipeline = self.client.pipelines.get_pipeline(
                project_id=self.test_config.project_id, pipeline_id=basic_pipeline["id"]
            )
            break

        assert pipeline is not None

        raw_yaml = self.client.pipelines.preview(
            project_id=self.test_config.project_id, pipeline_id=12778
        )
        data = yaml.safe_load(raw_yaml)
        assert data is not None

        run = None

        for base_run in self.client.pipelines.get_top_ten_thousand_runs(
            project_id=self.test_config.project_id, pipeline_id=pipeline["id"]
        ):
            run = self.client.pipelines.get_run(
                project_id=self.test_config.project_id,
                pipeline_id=pipeline["id"],
                run_id=base_run["id"],
            )
            break

        assert run is not None

    def test_get_groups_users(self):
        """Test getting groups/users."""

        project_descriptor = self.client.graph.get_scope_descriptors(self.test_config.project_id)

        for group in self.client.graph.list_groups(scope_descriptor=project_descriptor["value"]):
            details = self.client.graph.get_group(group["descriptor"])
            self.assertIsNotNone(details)
            for member in self.client.graph.list_users_in_container(group["descriptor"]):
                self.assertIsNotNone(member)
                break
            break

    def test_get_endpoints(self):
        """Test getting endpoints groups/users."""

        endpoints = self.client.endpoints.get_endpoints(
            project_id=self.test_config.project_id, endpoint_type="azurerm"
        )

        for endpoint in endpoints:
            for item in self.client.endpoints.get_usage_history(
                project_id=self.test_config.project_id, endpoint_id=endpoint["id"], top=75
            ):
                assert item is not None

        assert endpoints is not None

    def test_get_leases(self):
        """Remove a pipeline."""

        for pipeline in self.client.pipelines.get_pipelines(
            top=3, project_id=self.test_config.project_id
        ):
            pipeline_id = pipeline["id"]

            for build in self.client.builds.get_builds(
                project_id=self.test_config.project_id, definitions=[pipeline_id]
            ):
                leases = self.client.builds.get_leases(
                    project_id=self.test_config.project_id, build_id=build["id"]
                )

                assert leases is not None
                break

    def test_get_definitions(self):
        """Get definitions."""

        for definition in self.client.builds.get_definitions(
            project_id=self.test_config.project_id
        ):
            definition_id = definition["id"]

            full_definition = self.client.builds.get_definition(
                project_id=self.test_config.project_id, definition_id=definition_id
            )

            assert full_definition is not None
