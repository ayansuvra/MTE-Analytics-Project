"""
funnel_analysis.py

Reusable functions for funnel metrics and SLA breach flagging,
used across notebooks 02, 03, and 04.
"""

import pandas as pd

def build_funnel_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the reconciled patient funnel table.

    Stage order reflects the verified sequence:
    Inquiry -> Consultation Booked -> Quote Shared -> Treatment Completed
    -> Follow-up Completed (post-treatment).

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned patient_journey dataframe.

    Returns
    -------
    pd.DataFrame
        Funnel table with patient_count, conversion_from_prev, and
        drop_off_rate per stage.
    """
    funnel_counts = {
        "Inquiry": len(df),
        "Consultation Booked": df["consultation_booked"].sum(),
        "Quote Shared": df["quote_shared"].sum(),
        "Treatment Completed": df["treatment_completed"].sum(),
        "Follow-up Completed": df["follow_up_completed"].sum(),
    }
    funnel_df = pd.DataFrame(
        list(funnel_counts.items()), columns=["stage", "patient_count"]
    )
    funnel_df["conversion_from_prev"] = (
        funnel_df["patient_count"] / funnel_df["patient_count"].shift(1)
    )
    funnel_df["drop_off_count"] = (
        funnel_df["patient_count"].shift(1) - funnel_df["patient_count"]
    )
    funnel_df["drop_off_rate"] = (
        funnel_df["drop_off_count"] / funnel_df["patient_count"].shift(1)
    )
    return funnel_df


def flag_sla_breach(
    df: pd.DataFrame,
    country_reference: pd.DataFrame,
    response_col: str = "response_time_hours",
    baseline_col: str = "baseline_response_expectation_hours",
) -> pd.DataFrame:
    """
    Merge country-level baseline SLA and flag patients whose response
    time breached the expected baseline.

    Parameters
    ----------
    df : pd.DataFrame
        Patient journey dataframe (must contain 'country' and response_col).
    country_reference : pd.DataFrame
        Country reference dataframe (must contain 'country' and baseline_col).

    Returns
    -------
    pd.DataFrame
        Copy of df with a new boolean column 'sla_breach'.
    """
    merged = df.merge(
        country_reference[["country", baseline_col]], on="country", how="left"
    )
    merged["sla_breach"] = merged[response_col] > merged[baseline_col]
    return merged


def leak_safe_provider_performance(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    provider_col: str = "provider_id",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute provider historical performance on the TRAIN set only, then
    map those fixed rates onto both train and test to avoid target leakage.

    Parameters
    ----------
    train_df, test_df : pd.DataFrame
        Feature dataframes (must include provider_col).
    target_col : str
        Name of the target column, present in train_df (and joined in
        by the caller before calling this, or passed via train_df).

    Returns
    -------
    (train_df, test_df) with a new 'provider_performance' column added.
    """
    provider_rates = train_df.groupby(provider_col)[target_col].mean()
    overall_mean = train_df[target_col].mean()

    train_df = train_df.copy()
    test_df = test_df.copy()

    train_df["provider_performance"] = train_df[provider_col].map(provider_rates)
    test_df["provider_performance"] = test_df[provider_col].map(provider_rates)

    # Handle providers seen in test but not in train (fallback to overall mean)
    test_df["provider_performance"] = test_df["provider_performance"].fillna(
        overall_mean
    )

    return train_df, test_df