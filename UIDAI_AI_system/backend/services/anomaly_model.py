from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run IsolationForest on numeric columns and add:
    - anomaly (-1 for anomaly, 1 for normal)
    - is_anomaly (1 for anomaly, 0 for normal)

    Returns updated DataFrame and anomaly metadata.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # If no numeric columns, cannot run model
    if not numeric_cols:
        # Create default columns with no anomalies
        df["anomaly"] = 1
        df["is_anomaly"] = 0
        meta = {
            "numeric_features_used": [],
            "model_trained": False,
            "contamination": contamination,
        }
        return df, meta

    X = df[numeric_cols].values

    # IsolationForest for unsupervised anomaly detection
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X)
    preds = model.predict(X)  # 1 for normal, -1 for anomaly

    df["anomaly"] = preds
    df["is_anomaly"] = (preds == -1).astype(int)

    meta: Dict[str, Any] = {
        "numeric_features_used": numeric_cols,
        "model_trained": True,
        "contamination": contamination,
        "n_samples": len(df),
        "n_anomalies": int(df["is_anomaly"].sum()),
    }

    return df, meta
