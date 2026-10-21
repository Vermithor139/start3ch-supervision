from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

app = FastAPI(title="Verum ECN Financial Terminal")

BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def read_root():
    """Serves the main Supervisor / Broker Terminal view."""
    return FileResponse(BASE_DIR / "dashboard.html")

@app.get("/client", response_class=HTMLResponse)
async def read_client_portal():
    """Serves the Client Trading Portal interface (matching Bit Trady / client spec)."""
    client_html_path = BASE_DIR / "client.html"
    if client_html_path.exists():
        return FileResponse(client_html_path)
    return FileResponse(BASE_DIR / "dashboard.html")