#!/bin/bash

# Run unit tests (fast, no credentials needed)
python -m pytest tests/unit --cov=simple_ado --cov-report html --cov-report xml --junitxml=junit/test-results.xml

# To run integration tests (requires ADO credentials), use:
# python -m pytest tests --integration --cov=simple_ado --cov-report html --cov-report xml --junitxml=junit/test-results.xml
