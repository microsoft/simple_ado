"""Custom types for the library.

.. deprecated::
    This module is deprecated. Use :mod:`simple_ado.ado_types` instead.
    This module shadows the stdlib ``types`` module and will be removed in a
    future major version.
"""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# pylint: disable=wildcard-import,unused-wildcard-import,useless-import-alias

# Re-export everything from ado_types for backward compatibility.
from simple_ado.ado_types import *  # noqa: F401,F403
from simple_ado.ado_types import TeamFoundationId as TeamFoundationId  # noqa: F811
