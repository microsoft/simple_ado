# simple_ado

`simple_ado` is a Python wrapper around the Azure DevOps REST API.

Why does it exist when there is an existing Python SDK for the ADO API? 

Simply put, it's because the existing one is very complex and difficult to use. This version aims to be as simple as possible to use.


# Contributing

Runtime dependencies use compatible-version ranges in `pyproject.toml`; development dependencies
are pinned to exact versions in its `dev` group.
When updating them, refresh `poetry.lock` with `poetry lock` and run the checks below.

```sh
poetry install
poetry run black --check --line-length 100 simple_ado tests
poetry run pylint --rcfile=pylintrc simple_ado tests
poetry run mypy --strict --ignore-missing-imports simple_ado/ tests/
poetry run pyright simple_ado/ tests/
poetry run pytest tests/unit/ --cov=simple_ado
poetry check --lock
poetry build
```

# Releasing

To bump the version and publish a new release, run **Actions > Publish to PyPI > Run workflow**
from the default branch. Check **publish** and select **patch**, **minor**, or **major** for
**version_type**. The workflow updates `pyproject.toml` with `poetry version`, builds the package,
commits the version bump, atomically pushes the commit and a `v<version>` tag, and creates a
GitHub release. It then publishes to PyPI and attaches signed distributions to the release.
Publishing stays in the same workflow run because releases created using `GITHUB_TOKEN` do
not trigger another release workflow.

Leave **version_type** as **none** to publish the existing version without committing or tagging.
With **publish** unchecked (the default), this uploads to **TestPyPI**, not a dry run.
Publishing a GitHub release manually also continues to publish its existing version to PyPI;
pushing a tag alone does not trigger this workflow.

Before bumping a release, configure the **RELEASE_TOKEN** Actions secret with repository contents
write permission and an identity allowed to bypass the default branch's required checks and any
other applicable branch/tag rules. It is used only for the checkout and version commit/tag push
on version-bump runs. Creating the GitHub release still uses `GITHUB_TOKEN` to avoid duplicate
publishing runs. Existing-version publishing does not require `RELEASE_TOKEN`.
PyPI and TestPyPI must have trusted
publishing configured for `publish.yml` and their respective `pypi` and `testpypi` environments.
If publishing fails after the tag/release is created, rerun the failed jobs rather than starting
another version bump.

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
