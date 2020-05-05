"""ADO Operations."""

import enum
from typing import Any, Dict, Optional


class OperationType(enum.Enum):
    """An ADO operation."""

    add = "add"
    copy = "copy"
    move = "move"
    remove = "remove"
    replace = "replace"
    test = "test"


class PatchOperation:
    """Represents a PATCH operation."""

    def __init__(
        self,
        operation: OperationType,
        path: str,
        value: Optional[Any],
        from_path: Optional[str] = None,
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

    def serialize(self) -> Dict[str, str]:
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
        super().__init__(OperationType.add, field, value)


class DeleteOperation(PatchOperation):
    """Represents a delete PATCH operation."""

    def __init__(self, field: str):
        super().__init__(OperationType.remove, field, None)
