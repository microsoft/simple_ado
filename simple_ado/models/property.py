"""Property handling."""

import datetime
from typing import Any, Dict

import deserialize


@deserialize.key("property_type", "$type")
@deserialize.downcast_field("$type")
class PropertyValue:
    """Represents a property value."""

    property_type: str
    value: Any

    def __init__(self, property_type: str) -> None:
        self.property_type = property_type
        self.value = None

    def serialize(self) -> Dict[str, Any]:
        """Serialize to an ADO compatible format.

        :returns: A dictionary to be sent to ADO
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        try:
            return str(self.serialize())
        except NotImplementedError:
            return str({"$type": self.property_type, "$value": None})


@deserialize.key("value", "$value")
@deserialize.downcast_identifier(PropertyValue, "System.String")
class StringPropertyValue(PropertyValue):
    """Represents a string property value."""

    value: str

    def __init__(self, value: str) -> None:
        """Create a new string property value.

        :param value: The value of the property
        """
        super().__init__("System.String")
        self.value = value

    def serialize(self) -> Dict[str, Any]:
        """Serialize to an ADO compatible format.

        :returns: A dictionary to be sent to ADO
        """
        return {"$type": self.property_type, "$value": self.value}


@deserialize.key("value", "$value")
@deserialize.downcast_identifier(PropertyValue, "System.Int32")
class IntPropertyValue(PropertyValue):
    """Represents an int property value."""

    value: int

    def __init__(self, value: int) -> None:
        """Create a new int property value.

        :param value: The value of the property
        """
        super().__init__("System.Int32")
        self.value = value

    def serialize(self) -> Dict[str, Any]:
        """Serialize to an ADO compatible format.

        :returns: A dictionary to be sent to ADO
        """
        return {"$type": self.property_type, "$value": self.value}


@deserialize.key("value", "$value")
@deserialize.downcast_identifier(PropertyValue, "System.DateTime")
class DateTimePropertyValue(PropertyValue):
    """Represents an int property value."""

    value: datetime.datetime

    def __init__(self, value: datetime.datetime) -> None:
        """Create a new int property value.

        :param value: The value of the property
        """
        super().__init__("System.DateTime")
        self.value = value

    def serialize(self) -> Dict[str, Any]:
        """Serialize to an ADO compatible format.

        :returns: A dictionary to be sent to ADO
        """
        return {
            "$type": self.property_type,
            "$value": (
                self.value.strftime("%Y-%m-%dT%H:%M:%S.")
                + str(int(self.value.microsecond / 10000))
                + "Z"
            ),
        }
