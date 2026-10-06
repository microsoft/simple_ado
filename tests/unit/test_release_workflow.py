"""Regression tests for the manual release workflow's shell steps."""

import os
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest
import yaml


@pytest.fixture(name="release_steps")
def fixture_release_steps() -> dict[str, dict[str, Any]]:
    """Load release steps by name from the workflow."""
    workflow_path = Path(__file__).resolve().parents[2] / ".github/workflows/publish.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    return {step["name"]: step for step in workflow["jobs"]["build"]["steps"]}


@pytest.mark.parametrize(
    ("version_type", "publish", "ref", "has_token", "expected_error"),
    [
        ("none", "false", "refs/heads/feature", "false", ""),
        ("", "true", "refs/tags/v5.1.1", "false", ""),
        ("none", "true", "refs/tags/v5.1.1", "false", ""),
        ("patch", "true", "refs/heads/main", "true", ""),
        ("minor", "true", "refs/heads/main", "true", ""),
        ("major", "true", "refs/heads/main", "true", ""),
        ("patch", "false", "refs/heads/main", "true", "Version bumps require publish=true"),
        ("minor", "true", "refs/heads/feature", "true", "default branch"),
        ("major", "true", "refs/tags/v5.1.1", "true", "default branch"),
        ("patch", "true", "refs/heads/main", "false", "Configure RELEASE_TOKEN"),
        ("invalid", "true", "refs/heads/main", "true", "Invalid version type"),
    ],
)
def test_validate_release_inputs(
    release_steps: dict[str, dict[str, Any]],
    version_type: str,
    publish: str,
    ref: str,
    has_token: str,
    expected_error: str,
) -> None:
    """Allow legacy publishing while rejecting unsafe version-bump requests."""
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", release_steps["Validate release inputs"]["run"]],
        env={
            **os.environ,
            "VERSION_TYPE": version_type,
            "PUBLISH": publish,
            "GITHUB_REF": ref,
            "DEFAULT_BRANCH": "main",
            "HAS_RELEASE_TOKEN": has_token,
        },
        capture_output=True,
        text=True,
        check=False,
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
    release_steps: dict[str, dict[str, Any]],
    tmp_path: Path,
    version_type: str,
    expected_version: str,
) -> None:
    """Verify Poetry updates the package version and emits the matching release tag."""
    project_file = tmp_path / "pyproject.toml"
    project_file.write_text(
        '[tool.poetry]\nname = "release-test"\nversion = "1.2.3"\n'
        'description = "Release test"\nauthors = []\n',
        encoding="utf-8",
    )
    output_file = tmp_path / "output"
    subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", release_steps["Bump version number"]["run"]],
        cwd=tmp_path,
        env={**os.environ, "VERSION_TYPE": version_type, "GITHUB_OUTPUT": str(output_file)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert f'version = "{expected_version}"' in project_file.read_text(encoding="utf-8")
    assert output_file.read_text(encoding="utf-8") == f"release_tag=v{expected_version}\n"


def test_release_push_is_atomic(release_steps: dict[str, dict[str, Any]]) -> None:
    """Keep the commit and tag together, and use the non-recursive token for the release."""
    release_step = release_steps["Commit, tag, and create GitHub release"]
    commands = cast(str, release_step["run"])
    assert 'git push --atomic origin "HEAD:$GITHUB_REF" "refs/tags/$RELEASE_TAG"' in commands
    assert commands.index("git push --atomic") < commands.index("gh release create")
    assert release_step["env"]["GH_TOKEN"] == "${{ github.token }}"
    step_names = list(release_steps)
    assert step_names.index("Build package") < step_names.index(release_step["name"])
    assert step_names.index("Store the distribution packages") < step_names.index(
        release_step["name"]
    )
