#!/usr/bin/env python3

"""Generate synchronous code from the async source of truth.

This script transforms the async code in simple_ado/_async/ into synchronous
code at the top level of simple_ado/. The async code is the source of truth;
the sync code is generated and should not be edited by hand.

Usage:
    python scripts/generate_sync.py
"""

import os
import py_compile
import re
import sys
from typing import Callable

import black

# Directories
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASYNC_DIR = os.path.join(REPO_ROOT, "simple_ado", "_async")
SYNC_DIR = os.path.join(REPO_ROOT, "simple_ado")
ASYNC_TEST_DIR = os.path.join(REPO_ROOT, "tests", "unit", "_async")
SYNC_TEST_DIR = os.path.join(REPO_ROOT, "tests", "unit")

BLACK_MODE = black.Mode(line_length=100)


def _format_with_black(source: str) -> str:
    """Format source code with black. Returns source unchanged if black fails."""
    try:
        return black.format_str(source, mode=BLACK_MODE)
    except black.NothingChanged:
        return source
    except Exception:
        return source


# Files that are shared (not generated from _async/) and should not be overwritten
SHARED_FILES = {
    "ado_types.py",
    "comments.py",
    "exceptions.py",
}

# Header to mark generated files
GENERATED_HEADER = "# THIS FILE IS AUTO-GENERATED FROM simple_ado/_async/{}. DO NOT EDIT.\n\n"


def transform_source(source: str, relative_path: str) -> str:
    """Transform async Python source code to synchronous equivalent.

    :param source: The async source code
    :param relative_path: The relative path of the source file (for the header)
    :returns: The transformed synchronous source code
    """

    result = source

    # --- Import transformations ---

    # azure.identity.aio → azure.identity
    result = result.replace("azure.identity.aio", "azure.identity")

    # simple_ado._async.foo → simple_ado.foo  (with trailing dot, e.g. in from simple_ado._async.audit)
    result = result.replace("simple_ado._async.", "simple_ado.")
    # simple_ado._async → simple_ado  (without trailing dot, e.g. in from simple_ado._async import)
    result = result.replace("simple_ado._async", "simple_ado")

    # --- Class name transformations ---
    # ADOAsync* → ADO* everywhere (identifiers, __all__ strings, type annotations).
    # The ADOAsync prefix is unique enough that false positives in error messages
    # are not a concern.
    result = re.sub(r"\bADOAsync(\w+)", r"ADO\1", result)

    # --- async/await removal ---

    # async def → def
    result = re.sub(r"\basync def\b", "def", result)

    # await expr — strip the await keyword
    # Handle multi-line await (await on its own line followed by continuation)
    result = re.sub(r"\bawait ", "", result)

    # async with → with
    result = re.sub(r"\basync with\b", "with", result)

    # async for → for
    result = re.sub(r"\basync for\b", "for", result)

    # --- Restore yield from ---
    # async generators can't use "yield from", so the async source uses
    # "for item in x: yield item". In sync generators we can restore the
    # more concise "yield from x" — but only when the yield is the ONLY
    # statement in the loop body (i.e. the next non-blank line is dedented).
    result = re.sub(
        r"for (\w+) in (.+):\n(\s+)yield \1\n(?=\S|\s*\n\s*(?!\3\S))",
        r"yield from \2\n",
        result,
    )

    # --- Type hint transformations ---

    # AsyncIterator → Iterator
    result = result.replace("AsyncIterator", "Iterator")

    # AsyncGenerator → Generator
    result = result.replace("AsyncGenerator", "Generator")

    # Deduplicate imports that may appear after AsyncIterator → Iterator when the
    # source already imported Iterator alongside AsyncIterator.
    result = re.sub(r"\bIterator,\s*Iterator\b", "Iterator", result)

    # --- httpx client transformations ---

    # httpx.AsyncClient → httpx.Client
    result = result.replace("httpx.AsyncClient", "httpx.Client")

    # --- Async method name transformations ---

    # response.aiter_bytes → response.iter_bytes
    result = result.replace(".aiter_bytes(", ".iter_bytes(")

    # client.aclose() → client.close()
    result = result.replace(".aclose()", ".close()")

    # response.aread() → response.read()
    result = result.replace(".aread()", ".read()")

    # --- asyncio transformations ---

    # asyncio.to_thread(fn, args) → fn(args) — sync doesn't need thread offloading.
    # First handle the case with arguments: asyncio.to_thread(fn, arg1, arg2)
    result = re.sub(r"asyncio\.to_thread\(([^,]+),\s*", r"\1(", result)
    # Then handle the no-args case: asyncio.to_thread(fn)
    result = re.sub(r"asyncio\.to_thread\(([^)]+)\)", r"\1()", result)

    # asyncio.sleep → time.sleep
    result = result.replace("asyncio.sleep(", "time.sleep(")

    # --- Import cleanup ---

    # import asyncio → import time (only if asyncio is used solely for sleep)
    result = result.replace("import asyncio\n", "import time\n")

    # Remove pytest_asyncio import (becomes unused in sync tests)
    result = result.replace("import pytest_asyncio\n", "")

    # Remove @pytest.mark.asyncio decorators
    result = re.sub(r"\s*@pytest\.mark\.asyncio\n", "\n", result)

    # Remove bare "import pytest" when it's no longer used after removing asyncio markers.
    # Only remove if pytest is not referenced elsewhere in the file.
    if "import pytest\n" in result:
        # Count references to "pytest." excluding the import line itself
        without_import = result.replace("import pytest\n", "", 1)
        if "pytest." not in without_import and "pytest," not in without_import:
            result = result.replace("import pytest\n", "")

    # --- Context manager transformations ---

    # asynccontextmanager → contextmanager
    result = result.replace("asynccontextmanager", "contextmanager")

    # --- Dunder method transformations ---

    # __aenter__ → __enter__
    result = result.replace("__aenter__", "__enter__")

    # __aexit__ → __exit__
    result = result.replace("__aexit__", "__exit__")

    # __setitem_async__ → __setitem__ (async workaround for sync __setitem__)
    result = result.replace("__setitem_async__", "__setitem__")

    # --- follow_redirects ↔ allow_redirects ---
    # The sync generated code uses httpx too, so follow_redirects stays.
    # No transformation needed here.

    # --- Docstring fixups ---

    # "(async)" → "" in module docstrings, cleaning up trailing space
    result = result.replace(" (async)", "")
    result = result.replace("(async)", "")

    # "async " in docstrings where it's a description word
    # Only replace in specific patterns to avoid over-matching
    result = result.replace("Async wrapper", "Wrapper")
    result = result.replace("Async auth", "Auth")
    result = result.replace("async auth", "auth")
    result = result.replace("async authentication", "authentication")
    result = result.replace("An async iterator", "An iterator")
    result = result.replace("an async iterator", "an iterator")

    # Remove "In the async version..." sentences from docstrings
    result = re.sub(r"\n\s+In the async version[^\n]*", "", result)

    # "async context manager" → "context manager" in docstrings
    result = result.replace("an async context manager", "a context manager")
    result = result.replace("async context manager", "context manager")

    # --- Import ordering fixup ---
    # After asyncio → time replacement, stdlib imports may be out of alphabetical order.
    # Fix the specific known case.
    result = result.replace("import time\nimport contextlib\n", "import contextlib\nimport time\n")

    # Add generated header after the shebang line (if present) so the shebang remains on line 1
    header = GENERATED_HEADER.format(relative_path)
    if result.startswith("#!"):
        # Insert after the shebang line
        newline_idx = result.index("\n")
        result = result[: newline_idx + 1] + header + result[newline_idx + 1 :]
    else:
        result = header + result

    return result


def _restore_sync_getitem(source: str) -> str:
    """Restore auto-refresh behavior in sync ADOWorkItem.__getitem__.

    The async __getitem__ cannot auto-refresh because Python does not support
    ``async def __getitem__``.  The sync version has no such limitation, so we
    restore the original behavior where ``work_item["field"]`` transparently
    refreshes from the server on a cache miss.

    :param source: The transformed sync work_item.py source
    :returns: The source with __getitem__ patched to auto-refresh
    :raises ValueError: If the expected pattern is not found (signals that the
        async source changed and this transform needs updating)
    """

    old = '''\
    def __getitem__(self, key: str | ADOWorkItemBuiltInFields) -> Any:
        """Get a field value from the work item.

        Supports both string field names and ADOWorkItemBuiltInFields enum values.

        :param key: The field name or ADOWorkItemBuiltInFields enum value

        :returns: The field value

        :raises KeyError: If the field is not found
        """
        # Convert enum to string value if needed
        field_name = key.value if isinstance(key, ADOWorkItemBuiltInFields) else key

        # Try to get from fields dict
        fields = self._data.get("fields", {})
        if field_name in fields:
            return fields[field_name]

        raise KeyError(f"Field '{field_name}' not found in work item {self.id}")'''

    new = '''\
    def __getitem__(self, key: str | ADOWorkItemBuiltInFields) -> Any:
        """Get a field value from the work item.

        Supports both string field names and ADOWorkItemBuiltInFields enum values.
        If the field is not present in the current data, the work item will be
        refreshed from the server to try to populate missing fields.

        :param key: The field name or ADOWorkItemBuiltInFields enum value

        :returns: The field value

        :raises KeyError: If the field is not found even after refresh
        """
        # Convert enum to string value if needed
        field_name = key.value if isinstance(key, ADOWorkItemBuiltInFields) else key

        # Try to get from fields dict
        fields = self._data.get("fields", {})
        if field_name in fields:
            return fields[field_name]

        # Field not found — refresh from server (sync only; async must use get_field())
        self._log.debug(f"Field '{field_name}' not found, refreshing work item")
        self.refresh()

        # Try again after refresh
        fields = self._data.get("fields", {})
        if field_name in fields:
            return fields[field_name]

        raise KeyError(f"Field '{field_name}' not found in work item {self.id}")'''

    result = source.replace(old, new)
    if result == source:
        raise ValueError(
            "Failed to apply sync __getitem__ post-transform in work_item.py — "
            "the expected pattern was not found. If the async __getitem__ changed, "
            "update _restore_sync_getitem() to match."
        )
    return result


def _add_sync_del(source: str) -> str:
    """Add __del__ to sync ADOHTTPClient for silent garbage-collection cleanup.

    httpx.Client emits ResourceWarning when garbage-collected without being
    closed.  requests.Session did not, so existing consumers never called
    close().  Adding __del__ preserves the old silent-GC behavior.

    :param source: The transformed sync http_client.py source
    :returns: The source with __del__ inserted after __exit__
    :raises ValueError: If the expected pattern is not found
    """

    anchor = '''\
    def __exit__(self, *args: Any) -> None:
        self.close()'''

    replacement = anchor + '''

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass'''

    result = source.replace(anchor, replacement)
    if result == source:
        raise ValueError(
            "Failed to apply __del__ post-transform in http_client.py — "
            "the expected __exit__ pattern was not found. If the async source "
            "changed, update _add_sync_del() to match."
        )
    return result


# Map of (rel_prefix, filename) → list of post-transform functions to apply
# after the standard async→sync transformation.
_POST_TRANSFORMS: dict[str, list[Callable[[str], str]]] = {
    "work_item.py": [_restore_sync_getitem],
    "http_client.py": [_add_sync_del],
}


def _apply_post_transforms(source: str, relative_path: str) -> str:
    """Apply any file-specific post-transforms to the generated sync source.

    :param source: The already-transformed sync source
    :param relative_path: The relative file path (e.g. "work_item.py")
    :returns: The source with post-transforms applied
    """
    for fn in _POST_TRANSFORMS.get(relative_path, []):
        source = fn(source)
    return source


def transform_init(source: str) -> str:
    """Transform the async __init__.py to be the sync top-level __init__.py.

    This is handled specially because the top-level __init__.py also needs to
    provide access to the _async subpackage.

    :param source: The async __init__.py source
    :returns: The transformed sync __init__.py
    """

    result = transform_source(source, "__init__.py")

    # Add async re-exports at the bottom
    async_exports = '''

# Async API access
from simple_ado import _async as aio  # noqa: F401 — provides simple_ado.aio namespace

__all__ += ["aio"]
'''
    result = result.rstrip() + "\n" + async_exports

    return result


def process_directory(async_dir: str, sync_dir: str, rel_prefix: str = "") -> None:
    """Recursively transform all .py files from async_dir to sync_dir.

    :param async_dir: The async source directory
    :param sync_dir: The sync output directory
    :param rel_prefix: The relative path prefix for logging
    """

    for entry in sorted(os.listdir(async_dir)):
        async_path = os.path.join(async_dir, entry)
        sync_path = os.path.join(sync_dir, entry)
        relative = os.path.join(rel_prefix, entry) if rel_prefix else entry

        if os.path.isdir(async_path):
            if entry.startswith("__pycache__"):
                continue
            os.makedirs(sync_path, exist_ok=True)
            process_directory(async_path, sync_path, relative)

        elif entry.endswith(".py"):
            with open(async_path, "r") as f:
                source = f.read()

            if entry == "__init__.py" and rel_prefix == "":
                # Top-level __init__.py gets special treatment
                transformed = transform_init(source)
            else:
                transformed = transform_source(source, relative)

            transformed = _apply_post_transforms(transformed, relative)
            transformed = _format_with_black(transformed)

            # Check that we're not overwriting a shared file
            if rel_prefix == "" and entry in SHARED_FILES:
                print(f"  SKIP (shared): {relative}")
                continue

            # Check if sync file exists and content is the same
            if os.path.exists(sync_path):
                with open(sync_path, "r") as f:
                    existing = f.read()
                if existing == transformed:
                    continue

            print(f"  Writing: {relative}")
            with open(sync_path, "w") as f:
                f.write(transformed)


def verify_generated_files(sync_dir: str) -> bool:
    """Verify all generated .py files compile successfully.

    :param sync_dir: The directory containing generated files
    :returns: True if all files compile, False otherwise
    """
    ok = True
    for root, _dirs, files in os.walk(sync_dir):
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as exc:
                print(f"  COMPILE ERROR: {path}: {exc}", file=sys.stderr)
                ok = False
    return ok


def check_directory(async_dir: str, sync_dir: str, rel_prefix: str = "") -> bool:
    """Check if generated files are in sync with async source (without writing).

    :param async_dir: The async source directory
    :param sync_dir: The sync output directory
    :param rel_prefix: The relative path prefix for logging
    :returns: True if all files are in sync
    """
    in_sync = True

    for entry in sorted(os.listdir(async_dir)):
        async_path = os.path.join(async_dir, entry)
        sync_path = os.path.join(sync_dir, entry)
        relative = os.path.join(rel_prefix, entry) if rel_prefix else entry

        if os.path.isdir(async_path):
            if entry.startswith("__pycache__"):
                continue
            if not check_directory(async_path, sync_path, relative):
                in_sync = False

        elif entry.endswith(".py"):
            if rel_prefix == "" and entry in SHARED_FILES:
                continue

            with open(async_path, "r") as f:
                source = f.read()

            if entry == "__init__.py" and rel_prefix == "":
                transformed = transform_init(source)
            else:
                transformed = transform_source(source, relative)

            transformed = _apply_post_transforms(transformed, relative)
            transformed = _format_with_black(transformed)

            if not os.path.exists(sync_path):
                print(f"  MISSING: {relative}")
                in_sync = False
            else:
                with open(sync_path, "r") as f:
                    existing = f.read()
                if existing != transformed:
                    print(f"  OUT OF SYNC: {relative}")
                    in_sync = False

    return in_sync


# --- Test generation ---

# Header for generated test files
GENERATED_TEST_HEADER = "# THIS FILE IS AUTO-GENERATED FROM tests/unit/_async/{}. DO NOT EDIT.\n\n"

# Test files that should not be generated (manually maintained in tests/unit/)
SHARED_TEST_FILES = {"__init__.py", "conftest.py"}


def transform_test_source(source: str, relative_path: str) -> str:
    """Transform an async test file to its synchronous equivalent.

    Applies the standard code transforms first, then test-specific transforms
    for pytest markers, fixture names, and imports.

    :param source: The async test source code
    :param relative_path: The relative path of the source file (for the header)
    :returns: The transformed synchronous test source code
    """

    # Apply all standard code transforms (async def → def, await removal, etc.)
    # Use a dummy relative path for the code header — we'll replace it with the test header.
    result = transform_source(source, relative_path)

    # Replace the auto-generated code header with a test-specific one
    code_header = GENERATED_HEADER.format(relative_path)
    test_header = GENERATED_TEST_HEADER.format(relative_path)
    result = result.replace(code_header, test_header)

    # --- Test-specific transforms ---

    # Remove @pytest.mark.asyncio lines (including indented ones in test classes)
    result = re.sub(r"^\s*@pytest\.mark\.asyncio\n", "", result, flags=re.MULTILINE)

    # @pytest_asyncio.fixture → @pytest.fixture
    result = result.replace("@pytest_asyncio.fixture", "@pytest.fixture")

    # Remove import pytest_asyncio lines
    result = re.sub(r"^import pytest_asyncio\n", "", result, flags=re.MULTILINE)

    # Fixture name transforms: _async_ → _ (e.g. mock_async_client → mock_client)
    result = result.replace("_async_", "_")

    # Remaining async_ prefix in identifiers (e.g. async_http_client → http_client)
    result = re.sub(r"\basync_(\w)", r"\1", result)

    return result


def _restore_sync_getitem_tests(source: str) -> str:
    """Replace the async __getitem__ test with sync auto-refresh tests.

    The async __getitem__ just raises KeyError on missing fields. The sync
    version auto-refreshes. This replaces the simple test with two tests that
    verify the auto-refresh behavior.

    :param source: The transformed sync test_work_item.py source
    :returns: The source with sync-specific __getitem__ tests
    :raises ValueError: If the expected pattern is not found
    """

    old = '''\
def test_work_item_getitem_missing_field_raises(
    mock_work_item_data: dict[str, Any],
    mock_workitems_client: ADOWorkItemsClient,
) -> None:
    """Test that accessing a non-existent field raises KeyError."""
    work_item = ADOWorkItem(
        data=mock_work_item_data,
        client=mock_workitems_client,
        project_id="test-project",
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        _ = work_item["NonExistent.Field"]'''

    new = '''\
@respx.mock
def test_work_item_getitem_missing_field_refreshes(
    mock_work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """Test that accessing a missing field auto-refreshes and returns the value."""
    refreshed_data = copy.deepcopy(mock_work_item_data)
    refreshed_data["fields"]["System.Reason"] = "Fixed"

    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=refreshed_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    assert work_item["System.Reason"] == "Fixed"


@respx.mock
def test_work_item_getitem_missing_field_raises_after_refresh(
    mock_work_item_data: dict[str, Any], mock_client: ADOClient, mock_project_id: str
) -> None:
    """Test that accessing a non-existent field raises KeyError after refresh."""
    respx.get(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=mock_work_item_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    with pytest.raises(KeyError):
        _ = work_item["NonExistent.Field"]'''

    result = source.replace(old, new)
    if result == source:
        raise ValueError(
            "Failed to apply sync __getitem__ test post-transform in test_work_item.py — "
            "the expected pattern was not found."
        )
    return result


def _restore_sync_setitem_test(source: str) -> str:
    """Replace the async set() test with sync __setitem__ test.

    The async version tests ``await work_item.set(key, value)`` because async
    ``__setitem__`` is not possible.  The sync version tests ``work_item[key] = value``.

    :param source: The transformed sync test_work_item.py source
    :returns: The source with sync __setitem__ test
    :raises ValueError: If the expected pattern is not found
    """

    old = '''\
@respx.mock
def test_work_item_set(
    mock_work_item_data: dict[str, Any],
    mock_client: ADOClient,
    mock_project_id: str,
) -> None:
    """Test setting a field using the async set method."""
    updated_data = copy.deepcopy(mock_work_item_data)
    updated_data["fields"]["System.Title"] = "New Title"

    respx.patch(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=updated_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    work_item.set("System.Title", "New Title")

    assert work_item["System.Title"] == "New Title"'''

    new = '''\
@respx.mock
def test_work_item_setitem(
    mock_work_item_data: dict[str, Any],
    mock_client: ADOClient,
    mock_project_id: str,
) -> None:
    """Test setting a field using setitem."""
    updated_data = copy.deepcopy(mock_work_item_data)
    updated_data["fields"]["System.Title"] = "New Title"

    respx.patch(
        url__startswith=f"https://{mock_client.http_client.tenant}.visualstudio.com/DefaultCollection/"
        + f"{mock_project_id}/_apis/wit/workitems/12345",
    ).mock(return_value=httpx.Response(200, json=updated_data))

    work_item = ADOWorkItem(
        data=copy.deepcopy(mock_work_item_data),
        client=mock_client.workitems,
        project_id=mock_project_id,
        log=logging.getLogger("test"),
    )

    work_item["System.Title"] = "New Title"

    assert work_item["System.Title"] == "New Title"'''

    result = source.replace(old, new)
    if result == source:
        raise ValueError(
            "Failed to apply sync __setitem__ test post-transform in test_work_item.py — "
            "the expected pattern was not found."
        )
    return result


# Post-transforms for generated test files
_TEST_POST_TRANSFORMS: dict[str, list[Callable[[str], str]]] = {
    "test_work_item.py": [_restore_sync_getitem_tests, _restore_sync_setitem_test],
}


def _apply_test_post_transforms(source: str, relative_path: str) -> str:
    """Apply any file-specific post-transforms to the generated sync test source.

    :param source: The already-transformed sync test source
    :param relative_path: The relative file path (e.g. "test_work_item.py")
    :returns: The source with post-transforms applied
    """
    for fn in _TEST_POST_TRANSFORMS.get(relative_path, []):
        source = fn(source)
    return source


def process_test_directory(async_dir: str, sync_dir: str) -> None:
    """Transform async test files to sync test files.

    :param async_dir: The async test source directory (tests/unit/_async/)
    :param sync_dir: The sync test output directory (tests/unit/)
    """

    for entry in sorted(os.listdir(async_dir)):
        async_path = os.path.join(async_dir, entry)
        sync_path = os.path.join(sync_dir, entry)

        if not entry.endswith(".py") or entry in SHARED_TEST_FILES:
            continue

        if os.path.isdir(async_path):
            continue

        with open(async_path, "r") as f:
            source = f.read()

        transformed = transform_test_source(source, entry)
        transformed = _apply_test_post_transforms(transformed, entry)
        transformed = _format_with_black(transformed)

        if os.path.exists(sync_path):
            with open(sync_path, "r") as f:
                existing = f.read()
            if existing == transformed:
                continue

        print(f"  Writing: tests/unit/{entry}")
        with open(sync_path, "w") as f:
            f.write(transformed)


def check_test_directory(async_dir: str, sync_dir: str) -> bool:
    """Check if generated test files are in sync with async test source.

    :param async_dir: The async test source directory
    :param sync_dir: The sync test output directory
    :returns: True if all files are in sync
    """
    in_sync = True

    for entry in sorted(os.listdir(async_dir)):
        async_path = os.path.join(async_dir, entry)

        if not entry.endswith(".py") or entry in SHARED_TEST_FILES:
            continue

        if os.path.isdir(async_path):
            continue

        sync_path = os.path.join(sync_dir, entry)

        with open(async_path, "r") as f:
            source = f.read()

        transformed = transform_test_source(source, entry)
        transformed = _apply_test_post_transforms(transformed, entry)
        transformed = _format_with_black(transformed)

        if not os.path.exists(sync_path):
            print(f"  MISSING: tests/unit/{entry}")
            in_sync = False
        else:
            with open(sync_path, "r") as f:
                existing = f.read()
            if existing != transformed:
                print(f"  OUT OF SYNC: tests/unit/{entry}")
                in_sync = False

    return in_sync


def main() -> int:
    """Main entry point."""

    check_only = "--check" in sys.argv

    if not os.path.isdir(ASYNC_DIR):
        print(f"Error: Async source directory not found: {ASYNC_DIR}", file=sys.stderr)
        return 1

    if check_only:
        print("Checking sync code is up to date with async source...")
        ok = True
        if not check_directory(ASYNC_DIR, SYNC_DIR):
            ok = False
        if os.path.isdir(ASYNC_TEST_DIR):
            if not check_test_directory(ASYNC_TEST_DIR, SYNC_TEST_DIR):
                ok = False
        if not ok:
            print()
            print("Error: Generated files are out of sync.", file=sys.stderr)
            print("Run 'python scripts/generate_sync.py' to regenerate.", file=sys.stderr)
            return 1
        print("All generated files are in sync.")
        return 0

    print("Generating sync code from async source...")
    print(f"  Source: {ASYNC_DIR}")
    print(f"  Output: {SYNC_DIR}")
    print()

    process_directory(ASYNC_DIR, SYNC_DIR)

    if os.path.isdir(ASYNC_TEST_DIR):
        print()
        print("Generating sync tests from async test source...")
        print(f"  Source: {ASYNC_TEST_DIR}")
        print(f"  Output: {SYNC_TEST_DIR}")
        print()
        process_test_directory(ASYNC_TEST_DIR, SYNC_TEST_DIR)

    print()
    print("Verifying generated files compile...")
    if not verify_generated_files(SYNC_DIR):
        print("Error: Some generated files failed to compile.", file=sys.stderr)
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
