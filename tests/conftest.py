"""Shared fixtures: active_table holds its tables in a module-level global,
so each test must start from a clean slate to avoid leaking state between tests.
"""

import pytest

from finanalyticsagent import active_table


@pytest.fixture(autouse=True)
def reset_active_table():
    active_table._active_tables = None
    yield
    active_table._active_tables = None
