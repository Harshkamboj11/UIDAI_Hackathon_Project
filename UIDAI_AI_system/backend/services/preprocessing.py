from typing import Tuple, Dict, List

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def _detect_date_columns(df: pd.DataFrame) -> List[str]:
    """
    Automatically detect date/time columns by dtype or name pattern.
    """
    date_cols = []

    # 1. By dtype
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.datetime64):
            date_cols.append(col)

    # 2. By heuristic on column names
    name_keywords = ["date", "time", "timestamp", "datetime"]
    for col in df.columns:
        lower = col.lower()
        if any(k in lower for k in name_keywords) and col not in date_cols:
            date_cols.append(col)

    return date_cols


def preprocess_dataframe(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Perform automatic preprocessing:
    - Remove duplicates
    - Remove rows that are completely null
    - Convert date columns to datetime
    - Detect numeric columns
    - Normalize numeric columns using StandardScaler

    Returns processed DataFrame and metadata.
    """
    meta: Dict[str, any] = {}

    # Basic cleanup
    initial_rows = len(df)
    df = df.drop_duplicates()
    after_dup_rows = len(df)
    df = df.dropna(how="all")
    after_dropna_rows = len(df)

    meta["initial_rows"] = initial_rows
    meta["after_duplicates_rows"] = after_dup_rows
    meta["after_dropna_rows"] = after_dropna_rows

    # Detect and convert date columns
    date_cols = _detect_date_columns(df)
    for col in date_cols:
        # errors='coerce' will convert invalid to NaT
        df[col] = pd.to_datetime(df[col], errors="coerce")

    meta["date_columns"] = date_cols

    # Detect numeric columns (excluding pure bool, date)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    meta["numeric_columns"] = numeric_cols

    # Apply StandardScaler to numeric columns
    scaler = None
    if numeric_cols:
        scaler = StandardScaler()
        # Fill remaining NaNs with column median before scaling
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        scaled_values = scaler.fit_transform(df[numeric_cols])
        df[numeric_cols] = scaled_values

    meta["scaler_used"] = bool(numeric_cols)

    return df, meta
