from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).parent

@app.get("/", response_class=HTMLResponse)
def read_supervisor_dashboard():
    dashboard_path = BASE_DIR / "dashboard.html"
    if dashboard_path.is_file():
        return dashboard_path.read_text(encoding="utf-8")
    return "<h1>Dashboard template not found</h1>", 404

@app.get("/client", response_class=HTMLResponse)
def read_client_portal():
    client_path = BASE_DIR / "client.html"
    if client_path.is_file():
        return client_path.read_text(encoding="utf-8")
    return "<h1>Client portal template not found</h1>", 404