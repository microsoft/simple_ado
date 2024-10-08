"""ADO Operations."""

import enum
from typing import Any


class OperationType(enum.Enum):
    """An ADO operation."""

    ADD = "add"
    COPY = "copy"
    MOVE = "move"
    REMOVE = "remove"
    REPLACE = "replace"
    TEST = "test"


class PatchOperation:
    """Represents a PATCH operation."""

    operation: OperationType
    path: str
    value: Any | None
    from_path: str | None

    def __init__(
        self,
        operation: OperationType,
        path: str,
        value: Any | None,
        from_path: str | None = None,
    ):
        """Create a new PatchOperation.

        :param operation: The raw operation to do
        :param path: The path it affects
        :param value: The new value
        :param from_path: The old path (if applicable)
        """
        self.operation = operation
        self.path = path
        self.value = value
        self.from_path = from_path

    def serialize(self) -> dict[str, Any]:
        """Serialize for sending to ADO.

        :returns: A dictionary.
        """

        raw_dict = {
            "op": self.operation.value,
            "value": self.value,
            "from": self.from_path,
            "path": self.path,
        }

        return raw_dict

    def __str__(self):
        return str(self.serialize())


class AddOperation(PatchOperation):
    """Represents an add PATCH operation."""

    def __init__(self, field: str, value: Any):
        super().__init__(OperationType.ADD, field, value)


class DeleteOperation(PatchOperation):
    """Represents a delete PATCH operation."""

    def __init__(self, field: str):
        super().__init__(OperationType.REMOVE, field, None)
