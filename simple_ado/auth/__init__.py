# THIS FILE IS AUTO-GENERATED FROM simple_ado/_async/auth/__init__.py. DO NOT EDIT.

"""Umbrella module for all authentication classes."""

from .ado_auth import ADOAuth
from .ado_basic_auth import ADOBasicAuth
from .ado_token_auth import ADOTokenAuth
from .ado_azid_auth import ADOAzIDAuth

# Set the module's public interface
__all__ = [
    "ADOAuth",
    "ADOBasicAuth",
    "ADOTokenAuth",
    "ADOAzIDAuth",
]
