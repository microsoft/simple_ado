"""Utilities for dealing with the ADO REST API."""

import logging
from typing import Callable

import requests

from simple_ado.exceptions import ADOHTTPException


def boolstr(value: bool) -> str:
    """Return a boolean formatted as string for ADO calls

    :param value: The value to format

    :returns: A string representation of the boolean value
    """
    return str(value).lower()


def download_from_response_stream(
    *,
    response: requests.Response,
    output_path: str,
    log: logging.Logger,
    callback: Callable[[int, int], None] | None = None,
) -> None:
    """Downloads a file from an already open response stream.

    :param response: The response to download from
    :param output_path: The path to write the file out to
    :param log: The log to use for progress updates
    :param callback: If supplied, this will be called on every new chunk to update progress to the caller

    :raises ADOHTTPException: If we fail to fetch the file for any reason
    """

    # A sensible modern value
    chunk_size = 1024 * 16

    if response.status_code < 200 or response.status_code >= 300:
        raise ADOHTTPException("Failed to fetch file", response)

    with open(output_path, "wb") as output_file:
        content_length_string = response.headers.get("content-length", "0")

        total_size = int(content_length_string)
        total_downloaded = 0

        for data in response.iter_content(chunk_size=chunk_size):
            total_downloaded += len(data)
            output_file.write(data)

            if callback is not None:
                callback(total_downloaded, total_size)

            if total_size != 0:
                progress = int((total_downloaded * 100.0) / total_size)
                log.info(f"Download progress: {progress}%")
