import os
import pandas as pd
from fastapi import HTTPException


def load_file_to_df(filepath: str) -> pd.DataFrame:
    """
    Load CSV or Excel file into a Pandas DataFrame.
    Automatically detects by file extension.
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Uploaded file not found on server")

    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(filepath)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Only CSV, XLSX, and XLS are allowed.",
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return df
