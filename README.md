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

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
