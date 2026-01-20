import os
import uuid
import shutil
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from services.data_loader import load_file_to_df
from services.preprocessing import preprocess_dataframe
from services.anomaly_model import detect_anomalies
from services.analysis import generate_insights
from services.visualization import generate_charts

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_UPLOAD_DIR = os.path.join(BASE_DIR, "temp_uploads")
CHART_OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "charts")
INSIGHT_OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "insights")

os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
os.makedirs(INSIGHT_OUTPUT_DIR, exist_ok=True)


def cleanup_old_files(directory: str, max_age_hours: int = 1):
    """
    Delete files older than max_age_hours to prevent disk bloat.
    """
    try:
        now = datetime.now()
        cutoff_time = now - timedelta(hours=max_age_hours)
        
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    os.remove(filepath)
                    print(f"🧹 Cleaned old file: {filename}")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


def clear_all_old_data():
    """
    Clear ALL previous analysis data before new request.
    """
    # Clean temp uploads (older than 1 hour)
    cleanup_old_files(TEMP_UPLOAD_DIR, max_age_hours=1)
    
    # Clear ALL charts (new analysis will regenerate)
    if os.path.exists(CHART_OUTPUT_DIR):
        for filename in os.listdir(CHART_OUTPUT_DIR):
            filepath = os.path.join(CHART_OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
        print("🧹 Cleared all old charts")
    
    # Clear insights older than 24 hours (keep recent ones)
    cleanup_old_files(INSIGHT_OUTPUT_DIR, max_age_hours=24)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Process file upload with automatic cleanup of old data.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only CSV, XLSX, and XLS are allowed.",
        )

    unique_id = str(uuid.uuid4())
    temp_filename = f"{unique_id}{ext}"
    temp_filepath = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

    # 🚀 AUTO-CLEANUP: Flush old data before processing
    clear_all_old_data()
    print(f"🔄 New analysis started: {unique_id}")

    try:
        # Save uploaded file
        with open(temp_filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process data
        df = load_file_to_df(temp_filepath)
        df_processed, preprocessing_meta = preprocess_dataframe(df)
        df_anomaly, anomaly_meta = detect_anomalies(df_processed)

        insights: Dict[str, Any] = generate_insights(
            df_anomaly,
            insights_output_dir=INSIGHT_OUTPUT_DIR,
            run_id=unique_id,
            anomaly_meta=anomaly_meta,
            preprocessing_meta=preprocessing_meta,
        )

        chart_paths = generate_charts(
            df_anomaly,
            charts_output_dir=CHART_OUTPUT_DIR,
            run_id=unique_id,
        )

        # Return only filenames for frontend
        chart_filenames = [os.path.basename(path) for path in chart_paths if os.path.exists(path)]

        response = {
            "message": "File processed successfully",
            "run_id": unique_id,
            "insights": insights,
            "charts": chart_filenames,
        }
        print(f"✅ Analysis complete. Generated {len(chart_filenames)} charts.")
        return JSONResponse(status_code=200, content=response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        # Always delete temp upload file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass
