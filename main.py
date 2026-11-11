import os
import json
import random
import requests
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

app = FastAPI(title="Verum Invest Tactical Mainframe", version="6.0.5")
BASE_DIR = Path(__file__).resolve().parent

# --- GOOGLE FIREBASE CONFIGURATION ---
FIREBASE_URL = "https://verumcrm-default-rtdb.firebaseio.com/"
# -------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_db():
    try:
        url = FIREBASE_URL + "verum_data.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data is None:
            return {
                "agents": ["ALL", "LUIS", "MARIA", "SANDRO", "JESSICA", "DAVID", "MARC", "NICOLAS", "PATRICIA", "JOE", "ANA", "JUAN", "FIORELLA", "ANDRES", "FERNANDO", "UNASSIGNED", "ADRIANO", "MAURICIO"],
                "clients": {},
                "timestamp": 0
            }
        return data
    except Exception as e:
        print(f"Error loading DB from Firebase: {e}")
        return {
            "agents": ["ALL", "LUIS", "MARIA", "SANDRO", "JESSICA", "DAVID", "MARC", "NICOLAS", "PATRICIA", "JOE", "ANA", "JUAN", "FIORELLA", "ANDRES", "FERNANDO", "UNASSIGNED", "ADRIANO", "MAURICIO"],
            "clients": {},
            "timestamp": 0
        }

def save_db(db):
    try:
        url = FIREBASE_URL + "verum_data.json"
        response = requests.put(url, json=db, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error saving DB to Firebase: {e}")
        return False

@app.middleware("http")
async def strict_ip_firewall(request: Request, call_next):
    ALLOWED_IPS = ["191.96.215.107", "41.81.195.117", "127.0.0.1", "localhost"]
    path = request.url.path
    
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
def get_database(): 
    db = load_db()
    return JSONResponse(content=db)

@app.post("/api/db/update")
async def update_database(request: Request):
    try:
        data = await request.json()
        incoming_last_sync = data.get('synced_at', 0)
        incoming_clients = data.get('clients', {})

        current_db = load_db()
        current_ts = current_db.get('timestamp', 0)
        current_clients = current_db.get('clients', {})

        print(f"🔍 Sync Check: Frontend last synced at {incoming_last_sync}, DB last updated at {current_ts}")
        print(f"🔍 Incoming clients: {len(incoming_clients)}, Current DB clients: {len(current_clients)}")

        if incoming_last_sync < current_ts:
            print("⚠️ STALE DATA DETECTED. Smart merging to protect status changes...")
            merged_clients = current_clients.copy()
            new_leads_added = 0
            
            # ONLY add new clients that don't exist in current DB
            # NEVER overwrite existing clients (this preserves status changes)
            for tx_id, client_data in incoming_clients.items():
                if tx_id not in merged_clients:
                    merged_clients[tx_id] = client_data
                    new_leads_added += 1
                    print(f"  + Added new lead: {tx_id} ({client_data.get('name', 'Unknown')})")
                else:
                    # Client exists in both - keep the CURRENT DB version (newer)
                    # This preserves status changes made by advisors
                    print(f"  = Keeping current version for: {tx_id} ({client_data.get('name', 'Unknown')})")
            
            current_db['clients'] = merged_clients
            current_db['timestamp'] = time.time() * 1000
            success = save_db(current_db)
            print(f"✅ Merge successful. Added {new_leads_added} new leads. Total clients: {len(merged_clients)}")
        else:
            print("✅ FRESH DATA. Overwriting...")
            data['timestamp'] = time.time() * 1000
            success = save_db(data)
            print(f"✅ Save successful. Total clients: {len(data.get('clients', {}))}")

        if success:
            return JSONResponse(content={"status": "success"})
        else:
            return JSONResponse(content={"status": "error", "message": "Firebase rejected."}, status_code=500)
    except Exception as e:
        print(f"❌ Update error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/leads/submit")
async def submit_lead(request: Request):
    try:
        data = await request.json()
        db = load_db()
        tx_id = 'TX-' + str(random.randint(100000, 999999))
        
        new_client = {
            "txId": tx_id, "agent": "UNASSIGNED", "name": data.get('name', 'Unknown'),
            "country": data.get('country', 'Unknown'), "flag": "🌎",
            "phone": data.get('phone', ''), "email": data.get('email', ''),
            "lastLogin": "Just now", "balance": 0, "withdrawn": 0, "deposit": 0,
            "status": "NEW LEAD", "retention": "NEW", "subStatus": "POTENTIAL",
            "source": data.get('source', 'Website Landing Page'),
            "comment": "Lead captured via Landing Page.",
            "comments": [], "transactions": [], "withdrawals": []
        }
        db['clients'][tx_id] = new_client
        db['timestamp'] = time.time() * 1000
        success = save_db(db)
        if success:
            return JSONResponse(content={"status": "success", "message": "Lead captured successfully."})
        else:
            return JSONResponse(content={"status": "error", "message": "Failed to save lead."}, status_code=500)
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