"""
data_cleaning.py

Reusable functions for data quality profiling and CSV/DB consistency
checks, used in notebook 01.
"""

import pandas as pd
import sqlite3


def profile_dataframe(df: pd.DataFrame, name: str = "dataframe") -> None:
    """
    Print a standard data-quality profile: shape, dtypes, nulls,
    duplicates. Used for every raw table in notebook 01.
    """
    print(f"===== Profile: {name} =====")
    print(f"Shape: {df.shape}")
    print("\nDtypes:")
    print(df.dtypes)

    print("\nMissing values (count / %):")
    nulls = df.isnull().sum()
    pct = (df.isnull().mean() * 100).round(2)
    null_summary = pd.DataFrame({"null_count": nulls, "null_pct": pct})
    print(null_summary[null_summary["null_count"] > 0])

    print(f"\nDuplicate rows: {df.duplicated().sum()}")
    if "patient_id" in df.columns:
        print(f"Duplicate patient_id: {df['patient_id'].duplicated().sum()}")
    print("\n")


def check_csv_db_consistency(
    csv_df: pd.DataFrame,
    db_table_name: str,
    conn: sqlite3.Connection,
    sort_key: str,
) -> bool:
    """
    Compare a CSV-loaded dataframe against its SQLite table counterpart
    after normalizing whitespace/dtype differences.

    Returns True if they match, False otherwise (and prints the
    mismatched columns).
    """
    db_df = pd.read_sql(f"SELECT * FROM {db_table_name}", conn)

    def normalize(df):
        df = df.copy()
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str).str.strip()
        return df.sort_values(sort_key).reset_index(drop=True)

    csv_norm = normalize(csv_df)
    db_norm = normalize(db_df)

    mismatched_cols = []
    for col in csv_norm.columns:
        if col not in db_norm.columns:
            continue
        mismatches = (
            csv_norm[col].astype(str).str.strip()
            != db_norm[col].astype(str).str.strip()
        ).sum()
        if mismatches > 0:
            mismatched_cols.append((col, mismatches))

    if mismatched_cols:
        print(f"Mismatches found in {db_table_name}: {mismatched_cols}")
        return False

    print(f"{db_table_name}: CSV and DB versions match.")
    return True


def check_orphan_keys(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    key: str,
    child_name: str = "child",
    parent_name: str = "parent",
) -> set:
    """
    Check for foreign-key values in child_df that don't exist in
    parent_df (orphan records).
    """
    orphans = set(child_df[key]) - set(parent_df[key])
    if orphans:
        print(f"{len(orphans)} orphan {key} values found in {child_name} "
              f"not present in {parent_name}: {list(orphans)[:10]}")
    else:
        print(f"No orphan {key} values between {child_name} and {parent_name}.")
    return orphans