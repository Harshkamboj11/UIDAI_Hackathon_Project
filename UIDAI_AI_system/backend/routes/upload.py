import os
import uuid
from typing import Dict, Any

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


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
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

    try:
        with open(temp_filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    try:
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

        # FIXED: Return ONLY filenames for frontend
        chart_filenames = [os.path.basename(path) for path in chart_paths if os.path.exists(path)]

        response = {
            "message": "File processed successfully",
            "run_id": unique_id,
            "insights": insights,
            "charts": chart_filenames,  # ["uuid_health.png", "uuid_time.png"]
        }
        return JSONResponse(status_code=200, content=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass
