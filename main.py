import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

app = FastAPI(title="Verum Invest Tactical Mainframe", version="5.2.0")
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "database.json"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_db():
    if DB_FILE.exists():
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"agents": ["ALL"], "clients": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

@app.middleware("http")
async def strict_ip_firewall(request: Request, call_next):
    ALLOWED_IPS = ["191.96.215.107", "41.81.195.117", "127.0.0.1", "localhost"]
    path = request.url.path
    
    public_routes = ["/client", "/client-login", "/health", "/favicon.ico", "/static", "/docs", "/openapi.json", "/api/db", "/api/db/update"]
    if any(path == route or path.startswith(route + "/") for route in public_routes):
        return await call_next(request)
    
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    real_ip_header = request.headers.get("X-Real-IP", "")
    client_host = request.client.host if request.client else "unknown"
    
    if forwarded_for:
        detected_ip = forwarded_for.split(",")[0].strip()
    elif real_ip_header:
        detected_ip = real_ip_header.strip()
    else:
        detected_ip = client_host

    if detected_ip in ["127.0.0.1", "localhost", "::1"]:
        return await call_next(request)

    if detected_ip not in ALLOWED_IPS:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>403 Forbidden | Verum Invest</title>
                <style>
                    body { background: #02040a; color: #ef4444; font-family: 'Courier New', monospace; 
                           display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .box { text-align: center; padding: 40px; border: 2px solid #ef4444; border-radius: 8px; 
                           background: rgba(239,68,68,0.05); max-width: 500px; box-shadow: 0 0 30px rgba(239,68,68,0.2); }
                    h1 { font-size: 4rem; margin: 0 0 10px 0; letter-spacing: 5px; }
                    h2 { color: #f8fafc; margin-bottom: 20px; font-size: 1.5rem; }
                    p { color: #94a3b8; font-size: 0.9rem; line-height: 1.6; margin-bottom: 10px; }
                    .ip { color: #0ea5e9; background: rgba(14,165,233,0.1); padding: 8px 16px; 
                          border-radius: 4px; font-size: 1rem; margin-top: 20px; display: inline-block; border: 1px solid #0ea5e9; }
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>403</h1>
                    <h2>ACCESS DENIED</h2>
                    <p>This terminal is restricted to authorized IP nodes only.</p>
                    <p>Your connection attempt has been logged and flagged by security.</p>
                    <div class="ip">DETECTED IP: """ + detected_ip + """</div>
                    <p style="margin-top: 30px; font-size: 0.75rem; color: #475569;">Verum Invest Security Protocol v5.2</p>
                </div>
            </body>
            </html>
            """,
            status_code=403
        )
    return await call_next(request)

@app.get("/api/db")
def get_database():
    return JSONResponse(content=load_db())

@app.post("/api/db/update")
async def update_database(request: Request):
    try:
        data = await request.json()
        save_db(data)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.get("/login", response_class=HTMLResponse)
def read_login(): return HTMLResponse(content=(BASE_DIR / "login.html").read_text(encoding="utf-8"))

@app.get("/client-login", response_class=HTMLResponse)
def read_client_login(): return HTMLResponse(content=(BASE_DIR / "client-login.html").read_text(encoding="utf-8"))

@app.get("/", response_class=HTMLResponse)
def read_dashboard(): return HTMLResponse(content=(BASE_DIR / "dashboard.html").read_text(encoding="utf-8"))

@app.get("/client", response_class=HTMLResponse)
def read_client_portal(): return HTMLResponse(content=(BASE_DIR / "client.html").read_text(encoding="utf-8"))

@app.get("/health")
def health_check(): return {"status": "online", "system": "Verum Invest Mainframe"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)