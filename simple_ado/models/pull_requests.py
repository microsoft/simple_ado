"""ADO Pull Request Models."""

import enum


class ADOPullRequestTimeRangeType(enum.Enum):
    """An ADO operation."""

    CREATED = "created"
    CLOSED = "closed"
