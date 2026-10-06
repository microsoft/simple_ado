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

Run **Actions > Prepare release PR > Run workflow** from `main` and select **patch**, **minor**,
or **major**. The workflow runs `poetry version` and opens a PR containing the `pyproject.toml`
change. Repeated runs update the same `release/version-bump` branch and PR.
Review the change and merge it normally after the required checks pass.

When a version change reaches `main`, **Publish to PyPI** builds that exact merged commit,
creates its `v<version>` tag and GitHub release, publishes to PyPI, and attaches signed
distributions. Dependency-only changes to `pyproject.toml` do not publish.
The publisher never pushes commits to `main`. Publishing stays in the same workflow run
because releases created using `GITHUB_TOKEN` do not trigger another release workflow.

## Release PR authentication

Install an organization-approved GitHub App on this repository with **Contents: read and write**
and **Pull requests: read and write**. Configure its client ID as the Actions variable
**RELEASE_APP_CLIENT_ID** and its private key as the Actions secret **RELEASE_APP_PRIVATE_KEY**.
The workflow requests a short-lived token scoped to this repository and those two permissions.
It uses the App token rather than `GITHUB_TOKEN` to create the PR and trigger normal PR checks.
No branch-protection bypass, administrative permission, or automatic merge is required.
The App installation and credentials must comply with organization policy.

Without an App, run `poetry version patch` (or `minor`/`major`) on your own branch and open a PR
yourself. The same post-merge publishing runs; neither manual PR creation nor publishing needs
the App credentials. There is no `RELEASE_TOKEN` requirement.

## Existing-version publishing

**Actions > Publish to PyPI > Run workflow** still publishes the selected ref's existing version.
Check **publish** for PyPI; leaving it unchecked uploads to **TestPyPI**, not a dry run.
Publishing a GitHub release manually also publishes its existing version to PyPI.
Pushing a tag alone does not trigger this workflow.

PyPI and TestPyPI must have trusted publishing configured for `publish.yml` and their respective
`pypi` and `testpypi` environments. Repository rules must allow Actions to create release tags;
protected-branch writes are not needed. If PyPI publishing fails after a tag/release is created,
rerun the failed jobs instead of preparing another bump or publishing that GitHub release again.

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
