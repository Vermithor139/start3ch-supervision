from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI(title="Verum Trady Terminal & Portal")

BASE_DIR = Path(__file__).resolve().parent

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the Broker / Supervisor Terminal."""
    html_content = Path(BASE_DIR / "dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)

@app.get("/client", response_class=HTMLResponse)
async def read_client_portal():
    """Serves the Client Trading Portal (eToro UI)."""
    client_path = BASE_DIR / "client.html"
    if client_path.exists():
        html_content = Path(client_path).read_text(encoding="utf-8")
        return HTMLResponse(content=html_content)
    # Fallback to dashboard if client.html doesn't exist
    html_content = Path(BASE_DIR / "dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)