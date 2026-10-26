import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn

app = FastAPI(title="Verum Trady Tactical Mainframe", version="2.0.0")

# Anchor paths to the exact location of main.py
BASE_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=HTMLResponse)
def read_supervisor_dashboard():
    dashboard_path = BASE_DIR / "dashboard.html"
    if dashboard_path.is_file():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard template not found</h1>", status_code=404)

@app.get("/client", response_class=HTMLResponse)
def read_client_portal():
    client_path = BASE_DIR / "client.html"
    if client_path.is_file():
        return HTMLResponse(content=client_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Client portal template not found</h1>", status_code=404)

@app.get("/health")
def health_check():
    return {"status": "online", "system": "Verum Trady Mainframe"}

# CRITICAL FIX: Render deployment startup block
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)