"""Regression tests for protected-branch release preparation and publishing."""

import os
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest
import yaml


@pytest.fixture(name="workflows")
def fixture_workflows() -> dict[str, Any]:
    """Load workflow configuration without YAML's implicit boolean conversion."""
    directory = Path(__file__).resolve().parents[2] / ".github/workflows"
    return {
        name: yaml.load((directory / f"{name}.yml").read_text(encoding="utf-8"), yaml.BaseLoader)
        for name in ("prepare-release", "publish")
    }


@pytest.fixture(name="prepare_steps")
def fixture_prepare_steps(workflows: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the PR preparation steps by name."""
    return {step["name"]: step for step in workflows["prepare-release"]["jobs"]["prepare"]["steps"]}


@pytest.fixture(name="publish_steps")
def fixture_publish_steps(workflows: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the publishing steps by name."""
    return {step["name"]: step for step in workflows["publish"]["jobs"]["build"]["steps"]}


def _git(directory: Path, *arguments: str) -> str:
    """Run Git only in the temporary repository owned by the test."""
    return subprocess.run(
        ["git", *arguments],
        cwd=directory,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture(name="project")
def fixture_project(tmp_path: Path) -> Path:
    """Create a minimal Poetry project with a committed starting version."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "release-test"\nversion = "1.2.3"\n'
        'description = "Release test"\nauthors = []\n'
        '[tool.poetry.dependencies]\npython = ">=3.10"\n',
        encoding="utf-8",
    )
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Release test")
    _git(tmp_path, "config", "user.email", "release-test@example.com")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _git(tmp_path, "config", "tag.gpgsign", "false")
    _git(tmp_path, "add", "pyproject.toml")
    _git(tmp_path, "commit", "-qm", "Initial version")
    return tmp_path


def _run_shell(
    command: str, directory: Path, variables: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run the actual workflow shell with GitHub's fail-fast settings."""
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", command],
        cwd=directory,
        env={**os.environ, **variables},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("version_type", "ref", "client_id", "has_key", "expected_error"),
    [
        ("patch", "refs/heads/main", "app-client-id", "true", ""),
        ("minor", "refs/heads/main", "app-client-id", "true", ""),
        ("major", "refs/heads/main", "app-client-id", "true", ""),
        ("patch", "refs/heads/feature", "app-client-id", "true", "default branch"),
        ("minor", "refs/tags/v1.2.3", "app-client-id", "true", "default branch"),
        ("patch", "refs/heads/main", "", "true", "Configure RELEASE_APP_CLIENT_ID"),
        ("patch", "refs/heads/main", "app-client-id", "false", "Configure RELEASE_APP_CLIENT_ID"),
        ("none", "refs/heads/main", "app-client-id", "true", "Invalid version type"),
        ("invalid", "refs/heads/main", "app-client-id", "true", "Invalid version type"),
    ],
)
def test_validate_release_inputs(
    prepare_steps: dict[str, dict[str, Any]],
    tmp_path: Path,
    version_type: str,
    ref: str,
    client_id: str,
    has_key: str,
    expected_error: str,
) -> None:
    """Reject invalid release requests before minting an App token or changing files."""
    result = _run_shell(
        prepare_steps["Validate release inputs"]["run"],
        tmp_path,
        {
            "VERSION_TYPE": version_type,
            "GITHUB_REF": ref,
            "DEFAULT_BRANCH": "main",
            "APP_CLIENT_ID": client_id,
            "HAS_APP_PRIVATE_KEY": has_key,
        },
    )
    if expected_error:
        assert result.returncode != 0
        assert expected_error in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("version_type", "expected_version"),
    [("patch", "1.2.4"), ("minor", "1.3.0"), ("major", "2.0.0")],
)
def test_bump_release_version(
    prepare_steps: dict[str, dict[str, Any]],
    project: Path,
    version_type: str,
    expected_version: str,
) -> None:
    """Verify preparation updates the version but never commits it to the base branch."""
    subprocess.run(
        ["poetry", "lock", "--no-interaction"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    )
    original_commit = _git(project, "rev-parse", "HEAD")
    output_file = project / "output"
    result = _run_shell(
        prepare_steps["Bump version number"]["run"],
        project,
        {"VERSION_TYPE": version_type, "GITHUB_OUTPUT": str(output_file)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'version = "{expected_version}"' in (project / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert output_file.read_text(encoding="utf-8") == f"release_tag=v{expected_version}\n"
    assert _git(project, "rev-parse", "HEAD") == original_commit


@pytest.mark.parametrize("new_version", ["1.2.3", "1.2.4", "1.3.0rc1"])
def test_detect_merged_version_change(
    publish_steps: dict[str, dict[str, Any]], project: Path, new_version: str
) -> None:
    """Publish version changes, not unrelated edits to package metadata."""
    before = _git(project, "rev-parse", "HEAD")
    project_file = project / "pyproject.toml"
    project_file.write_text(
        project_file.read_text(encoding="utf-8")
        .replace('version = "1.2.3"', f'version = "{new_version}"')
        .replace("Release test", "Updated description"),
        encoding="utf-8",
    )
    _git(project, "add", "pyproject.toml")
    _git(project, "commit", "-qm", "Merged package metadata")
    output = project / "output"
    output.touch()
    summary = project / "summary"
    result = _run_shell(
        publish_steps["Detect merged version change"]["run"],
        project,
        {"BEFORE_SHA": before, "GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    expected = "" if new_version == "1.2.3" else f"release_tag=v{new_version}\n"
    assert output.read_text(encoding="utf-8") == expected
    if not expected:
        assert "nothing to publish" in summary.read_text(encoding="utf-8")


def test_missing_previous_commit_fails(
    publish_steps: dict[str, dict[str, Any]], project: Path
) -> None:
    """Never infer a new release when the previous version cannot be read."""
    output = project / "output"
    output.touch()
    result = _run_shell(
        publish_steps["Detect merged version change"]["run"],
        project,
        {
            "BEFORE_SHA": "0" * 40,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(project / "summary"),
        },
    )
    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    "existing_tag", ["absent", "same", "annotated", "different", "remote-different"]
)
def test_release_targets_merged_commit(
    publish_steps: dict[str, dict[str, Any]], project: Path, existing_tag: str
) -> None:
    """Target the merged SHA and refuse to reuse a version pointing at different source."""
    tag = "v1.2.4"
    remote = project / "remote.git"
    _git(project, "init", "--bare", str(remote))
    _git(project, "remote", "add", "origin", str(remote))
    if existing_tag in ("different", "remote-different"):
        _git(project, "tag", tag)
    if existing_tag == "remote-different":
        _git(project, "push", "origin", f"refs/tags/{tag}")
        _git(project, "tag", "-d", tag)
    _git(project, "commit", "--allow-empty", "-qm", "Merged version bump")
    merged_sha = _git(project, "rev-parse", "HEAD")
    if existing_tag == "same":
        _git(project, "tag", tag)
    elif existing_tag == "annotated":
        _git(project, "tag", "-a", tag, "-m", "Annotated release")
    call_log = project / "gh-call"
    result = _run_shell(
        'gh() { printf "%s\\n" "$@" > "$CALL_LOG"; }\n'
        + publish_steps["Tag merged commit and create GitHub release"]["run"],
        project,
        {"RELEASE_TAG": tag, "GITHUB_SHA": merged_sha, "CALL_LOG": str(call_log)},
    )
    if existing_tag in ("different", "remote-different"):
        assert result.returncode != 0
        if existing_tag == "different":
            assert "already points at another commit" in result.stdout
        else:
            assert "already exists" in result.stderr
        assert not call_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert call_log.read_text(encoding="utf-8").splitlines() == [
            "release",
            "create",
            tag,
            "--verify-tag",
            "--title",
            f"Release {tag}",
            "--generate-notes",
        ]
        assert _git(project, f"--git-dir={remote}", "rev-parse", f"{tag}^{{commit}}") == merged_sha
    assert _git(project, "rev-parse", "HEAD") == merged_sha
    assert _git(project, f"--git-dir={remote}", "for-each-ref", "refs/heads") == ""


def test_pr_creation_uses_scoped_app_token(
    workflows: dict[str, Any], prepare_steps: dict[str, dict[str, Any]]
) -> None:
    """Keep release preparation separate from protected-branch writes and auto-merge."""
    assert workflows["prepare-release"]["permissions"] == {"contents": "read"}
    token_inputs = prepare_steps["Generate release App token"]["with"]
    assert token_inputs["permission-contents"] == "write"
    assert token_inputs["permission-pull-requests"] == "write"
    pr_inputs = prepare_steps["Create or update release PR"]["with"]
    assert pr_inputs["token"] == "${{ steps.app_token.outputs.token }}"
    assert pr_inputs["branch"] == "release/version-bump"
    assert pr_inputs["base"] == "${{ github.event.repository.default_branch }}"
    assert pr_inputs["add-paths"] == "pyproject.toml"
    assert "merge" not in pr_inputs


def test_publish_events_and_permissions(
    workflows: dict[str, Any], publish_steps: dict[str, dict[str, Any]]
) -> None:
    """Keep existing publishing paths and gate automatic releases on a real version change."""
    publish = workflows["publish"]
    assert publish["on"]["push"] == {"branches": ["main"], "paths": ["pyproject.toml"]}
    assert publish["on"]["release"] == {"types": ["published"]}
    assert set(publish["on"]["workflow_dispatch"]["inputs"]) == {"publish"}
    assert publish["on"]["workflow_dispatch"]["inputs"]["publish"]["default"] == "false"
    assert publish["concurrency"]["group"] == "publish-${{ github.sha }}"
    assert publish_steps["Checkout code"]["with"]["ref"] == "${{ github.sha }}"
    assert publish_steps["Checkout code"]["with"]["fetch-depth"] == "0"
    for step_name in ("Install dependencies", "Build package", "Store the distribution packages"):
        assert publish_steps[step_name]["if"] == (
            "github.event_name != 'push' || steps.version_change.outputs.release_tag != ''"
        )
    assert "needs.build.outputs.release_tag != ''" in publish["jobs"]["publish-to-pypi"]["if"]
    release_step = publish_steps["Tag merged commit and create GitHub release"]
    assert release_step["env"]["GH_TOKEN"] == "${{ github.token }}"
    step_names = list(publish_steps)
    assert step_names.index("Store the distribution packages") < step_names.index(
        release_step["name"]
    )
    for step in publish_steps.values():
        commands = cast(str, step.get("run", ""))
        for line in commands.splitlines():
            if "git push" in line:
                assert line == 'git push origin "refs/tags/$RELEASE_TAG"'
        assert "git commit" not in commands
