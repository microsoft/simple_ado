#!/bin/bash

pushd "${VIRTUAL_ENV}/.." > /dev/null

python -m black --line-length 100 simple_ado tests
python -m pylint --rcfile=pylintrc simple_ado tests
python -m mypy --ignore-missing-imports simple_ado/ tests/

popd > /dev/null

