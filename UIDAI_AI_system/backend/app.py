from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routes.upload import router as upload_router

app = FastAPI(
    title="UIDAI AI Data Insight Service",
    description="Production-ready AI-driven backend for dynamic dataset analysis and anomaly detection.",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(upload_router, prefix="/api")

# ADDED: Serve static charts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
