"""Guards against forgetting to list a bazaar_books demo file in app.py's
sidebar — exactly what happened once (realm_metadata.csv was added for the
multi-table prototype but not surfaced as a demo option in the app).

Reads app.py as text rather than importing it: app.py runs Streamlit
sidebar code at module level, so importing it outside a real `streamlit
run` context would fail.
"""

from pathlib import Path


def test_every_bazaar_books_csv_is_referenced_in_app_py():
    app_source = Path("app.py").read_text()
    demo_csvs = sorted(Path("bazaar_books").glob("*.csv"))

    assert demo_csvs, "expected at least one demo CSV in bazaar_books/"

    missing = [csv.name for csv in demo_csvs if csv.as_posix() not in app_source]

    assert not missing, f"bazaar_books files not referenced in app.py: {missing}"
