#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Tests for the package."""

# pylint: disable=line-too-long

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "..")))
import simple_ado


class LibraryTests(unittest.TestCase):
    """Basic tests."""

    def test_existence(self):
        """Test existence."""
        self.assertIsNotNone(simple_ado)
