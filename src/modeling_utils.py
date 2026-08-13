"""
modeling_utils.py

Reusable functions for leak-safe feature engineering and model
evaluation, used across notebook 04 for both prediction targets.
"""

import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    brier_score_loss,
    confusion_matrix,
)


def leak_safe_provider_performance(train_df, test_df, target_col, provider_col="provider_id"):
    """
    Compute provider historical performance on TRAIN only, then map the
    fixed rates onto both train and test. Prevents target leakage.
    """
    provider_rates = train_df.groupby(provider_col)[target_col].mean()
    overall_mean = train_df[target_col].mean()

    train_df = train_df.copy()
    test_df = test_df.copy()

    train_df["provider_performance"] = train_df[provider_col].map(provider_rates)
    test_df["provider_performance"] = test_df[provider_col].map(provider_rates)
    test_df["provider_performance"] = test_df["provider_performance"].fillna(overall_mean)

    return train_df, test_df


def evaluate_model(model, X_test, y_test, model_name="model"):
    """
    Compute standard evaluation metrics for a binary classifier.

    Returns
    -------
    dict with roc_auc, precision, recall, brier_score, and confusion_matrix
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    return {
        "model": model_name,
        "roc_auc": roc_auc_score(y_test, y_proba),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "brier_score": brier_score_loss(y_test, y_proba),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
    }


def build_metrics_table(results_list):
    """
    Combine multiple evaluate_model() outputs into a single comparison
    dataframe (drops the confusion matrix, which isn't tabular-friendly).
    """
    rows = [
        {k: v for k, v in r.items() if k != "confusion_matrix"}
        for r in results_list
    ]
    return pd.DataFrame(rows).set_index("model")