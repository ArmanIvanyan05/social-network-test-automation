"""Shared pytest state that is safe to import before plugin registration."""

import pytest

UI_TEST_FAILED = pytest.StashKey[bool]()
