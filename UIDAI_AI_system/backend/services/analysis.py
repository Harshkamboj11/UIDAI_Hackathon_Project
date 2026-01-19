import json
import os
from typing import Dict, Any, Optional
import pandas as pd


def generate_insights(df: pd.DataFrame, insights_output_dir: str, run_id: str,
                     anomaly_meta: Optional[Dict[str, Any]] = None,
                     preprocessing_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safe insights generation."""
    total_records = len(df)
    total_anomalies = int(df.get('is_anomaly', pd.Series(0)).sum())
    anomaly_pct = round((total_anomalies / total_records * 100), 2) if total_records else 0

    insights = {
        "run_id": run_id,
        "total_records": total_records,
        "total_anomalies": total_anomalies,
        "anomaly_percentage": anomaly_pct,
        "anomaly_meta": anomaly_meta or {},
        "preprocessing_meta": preprocessing_meta or {},
    }

    # Safe aggregations (optional)
    try:
        insights["aggregations"] = {
            "normal_count": total_records - total_anomalies,
            "health_status": "healthy" if anomaly_pct < 5 else "needs_attention"
        }
    except:
        pass

    os.makedirs(insights_output_dir, exist_ok=True)
    insight_file = os.path.join(insights_output_dir, f"{run_id}_insights.json")
    
    with open(insight_file, "w") as f:
        json.dump(insights, f, indent=2)
    
    insights["insight_file"] = insight_file
    return insights
