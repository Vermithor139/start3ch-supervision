import os
import json
import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

app = FastAPI(title="Verum Invest Tactical Mainframe", version="5.3.0")
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
    
    # Public routes (No IP check)
    public_routes = ["/client", "/client-login", "/health", "/favicon.ico", "/static", "/docs", "/openapi.json", "/api/db", "/api/db/update", "/api/leads/submit", "/lead-capture"]
    if any(path == route or path.startswith(route + "/") for route in public_routes):
        return await call_next(request)
    
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    real_ip_header = request.headers.get("X-Real-IP", "")
    client_host = request.client.host if request.client else "unknown"
    
    if forwarded_for: detected_ip = forwarded_for.split(",")[0].strip()
    elif real_ip_header: detected_ip = real_ip_header.strip()
    else: detected_ip = client_host

    if detected_ip in ["127.0.0.1", "localhost", "::1"]: return await call_next(request)

    if detected_ip not in ALLOWED_IPS:
        return HTMLResponse(
            content="""<!DOCTYPE html><html><head><style>body{background:#02040a;color:#ef4444;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}.box{text-align:center;padding:40px;border:2px solid #ef4444;border-radius:8px;background:rgba(239,68,68,0.05);}</style></head><body><div class="box"><h1>403 ACCESS DENIED</h1><p>IP: """ + detected_ip + """</p></div></body></html>""",
            status_code=403
        )
    return await call_next(request)

@app.get("/api/db")
def get_database(): return JSONResponse(content=load_db())

@app.post("/api/db/update")
async def update_database(request: Request):
    try:
        data = await request.json()
        save_db(data)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/leads/submit")
async def submit_lead(request: Request):
    try:
        data = await request.json()
        db = load_db()
        tx_id = 'TX-' + str(random.randint(100000, 999999))
        
        new_client = {
            "txId": tx_id,
            "agent": "UNASSIGNED",
            "name": data.get('name', 'Unknown'),
            "country": data.get('country', 'Unknown'),
            "flag": "🌎",
            "phone": data.get('phone', ''),
            "email": data.get('email', ''),
            "lastLogin": "Just now",
            "balance": 0, "withdrawn": 0, "deposit": 0,
            "status": "NEW LEAD",
            "retention": "NEW",
            "subStatus": "POTENTIAL",
            "source": data.get('source', 'Website Landing Page'),
            "comment": f"Lead captured via Landing Page. Source: {data.get('source', 'Direct')}",
            "comments": [], "transactions": [], "withdrawals": []
        }
        db['clients'][tx_id] = new_client
        save_db(db)
        return JSONResponse(content={"status": "success", "message": "Lead captured successfully."})
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

@app.get("/lead-capture", response_class=HTMLResponse)
def read_lead_capture(): return HTMLResponse(content=(BASE_DIR / "lead-capture.html").read_text(encoding="utf-8"))

@app.get("/health")
def health_check(): return {"status": "online", "system": "Verum Invest Mainframe"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)