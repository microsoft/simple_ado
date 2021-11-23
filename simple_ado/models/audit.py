"""ADO Operations."""

import enum

import deserialize


class AuditActionCategory(enum.Enum):
    """An AuditActionCategory."""

    ACCESS = "access"
    CREATE = "create"
    EXECUTE = "execute"
    MODIFY = "modify"
    REMOVE = "remove"
    UNKNOWN = "unknown"


@deserialize.key("action_id", "actionId")
class AuditActionInfo:
    """Represents an AuditActionInfo."""

    action_id: str
    area: str
    category: AuditActionCategory
