"""Shared fixtures: active_table holds its DataFrame in a module-level global,
so each test must start from a clean slate to avoid leaking state between tests.
"""

import pytest

from finanalyticsagent import active_table


@pytest.fixture(autouse=True)
def reset_active_table():
    active_table._active_df = None
    yield
    active_table._active_df = None
