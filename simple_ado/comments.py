#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""ADO comment utilities"""

import enum
from typing import Any


class ADOCommentStatus(enum.Enum):
    """Possible values of comment statuses."""

    ACTIVE: int = 1
    FIXED: int = 2
    WONT_FIX: int = 3
    CLOSED: int = 4
    BY_DESIGN: int = 5
    PENDING: int = 6


class ADOCommentProperty:
    """The properties a comment can take."""

    SUPPORTS_MARKDOWN = "Microsoft.TeamFoundation.Discussion.SupportsMarkdown"

    # This is just a unique property value to show that a comment was created by
    # this library. It allows for easy cleanup later.
    COMMENT_IDENTIFIER = "3533F9EC-9336-4290-85F7-6A6A51AD1861"

    @staticmethod
    def create_value(type_name: str, value: int | str) -> dict[str, Any]:
        """Create a new property value.

        :param type_name: The type of property
        :param value: The value of the property

        :returns: A dictionary containing the raw API data
        """
        return {"type": type_name, "value": value}

    @staticmethod
    def create_string(value: str) -> dict[str, Any]:
        """Create a new string value.

        :param value: The value of the property

        :returns: A dictionary containing the raw API data
        """
        return ADOCommentProperty.create_value("System.String", value)

    @staticmethod
    def create_int(value: int) -> dict[str, Any]:
        """Create a new integer value.

        :param value: The value of the property

        :returns: A dictionary containing the raw API data
        """
        return ADOCommentProperty.create_value("System.Int32", value)

    @staticmethod
    def create_bool(value: bool) -> dict[str, Any]:
        """Create a new boolean value.

        :param value: The value of the property

        :returns: A dictionary containing the raw API data
        """
        return ADOCommentProperty.create_int(1 if value else 0)


class ADOCommentLocation:
    """Represents the location of a comment in a PR.

    :param file_path: The location of the file, relative to the repository.
    :param line: The line the comment should start on.
    :param start_index: The location on the line that the comment should start
    :type start_index: int or None
    """

    file_path: str
    line: int
    start_index: int | None

    def __init__(self, file_path: str, line: int, start_index: int | None = None) -> None:
        """Construct a new comment location."""

        self.file_path = file_path
        self.line = line
        self.start_index = start_index

        if not self.file_path.startswith("/"):  # On some machines this is missing, some it's there
            self.file_path = "/" + self.file_path

    def generate_representation(self) -> dict[str, Any]:
        """Generate the ADO API representation of a comment location.

        :returns: A dictionary containing the raw API data
        """

        return {
            "filePath": self.file_path,
            "leftFileStart": None,
            "leftFileEnd": None,
            "rightFileStart": {
                "line": self.line,
                "offset": 0 if self.start_index is None else self.start_index,
            },
            "rightFileEnd": {
                "line": self.line,
                "offset": 9999,  # We have no way to get the actual length, so let's just pick a high number.
            },
        }


class ADOComment:
    """Represents a ADO comment."""

    content: str
    location: ADOCommentLocation | None
    parent_id: int

    def __init__(
        self,
        content: str,
        location: ADOCommentLocation | None = None,
        parent_id: int = 0,
    ) -> None:
        """Construct a new comment.

        :param content: The message which should be on the comment
        :param location: The location to place the comment
        :param parent_id: The ID of the parent comment (0 if a root comment)
        """

        self.content = content
        self.parent_id = parent_id
        self.location = location

    def generate_representation(self) -> dict[str, Any]:
        """Generate the ADO API representation of this comment.

        :returns: A dictionary containing the raw API data
        """
        return {
            "parentCommentId": self.parent_id,
            "content": self.content,
            "commentType": 1,  # Always set to 1 according to documentation
        }

    def __str__(self) -> str:
        """Generate and return the string representation of the object.

        :return: A string representation of the object
        """
        details = self.generate_representation()
        if self.location is None:
            details["location"] = None
        else:
            details["location"] = self.location.generate_representation()
        return str(details)

    def __repr__(self) -> str:
        """Returns a raw representation of the object which can be used to reconstruct it later.

        :returns: A raw representation of the object
        """
        return str(self)
