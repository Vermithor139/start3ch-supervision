import os
import json
import random
import re
import html as htmllib
import datetime
import asyncio
import requests
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

APP_VERSION = "6.0.17"

app = FastAPI(title="Verum Invest Tactical Mainframe", version=APP_VERSION)
BASE_DIR = Path(__file__).resolve().parent

FIREBASE_URL = "https://verumcrm-default-rtdb.firebaseio.com/"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
MANAGER_CHAT_ID = os.environ.get("MANAGER_CHAT_ID", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
TG_STATE = {}

NEWS_CACHE = {"ts": 0, "items": []}
NEWS_FEEDS = [
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== JARVIS MEMORY (log + approval queue, persisted in Firebase) =====
def _node_load(node, default):
    try:
        r = requests.get(FIREBASE_URL + node + ".json", timeout=10)
        data = r.json()
        return data if data is not None else default
    except Exception:
        return default

def _node_save(node, data):
    try:
        requests.put(FIREBASE_URL + node + ".json", json=data, timeout=10)
    except Exception as e:
        print(f"Persist error ({node}): {e}")

BOT_LOG = (_node_load("bot_log", []) or [])[-100:]
BOT_QUEUE = _node_load("bot_queue", []) or []
STATS_CACHE = {"ts": 0, "data": {}}
LAST_BRIEF_DAY = None

def bot_log_add(entry_type, message, status="ok"):
    entry = {"ts": time.time() * 1000, "type": entry_type, "message": message, "status": status}
    BOT_LOG.append(entry)
    while len(BOT_LOG) > 100:
        BOT_LOG.pop(0)
    _node_save("bot_log", BOT_LOG)
    print(f"🤖 [{entry_type}] {message}")
    return entry

def queue_add(item):
    BOT_QUEUE.append(item)
    _node_save("bot_queue", BOT_QUEUE)

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

def _strip_tags(s):
    return re.sub('<[^<]+>', '', s or '').strip()

def _parse_dt(s):
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

# ===== TELEGRAM BOT ENGINE =====
async def tg_call(method, **params):
    if not TELEGRAM_BOT_TOKEN:
        return {}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, lambda: requests.post(url, json=params, timeout=20))
        return resp.json()
    except Exception as e:
        print(f"Telegram API error ({method}): {e}")
        return {}

def save_telegram_lead(name, country, phone, deposit, tg_username="", tg_chat_id=None):
    db = load_db()
    tx_id = 'TX-' + str(random.randint(100000, 999999))
    now = time.time() * 1000
    new_client = {
        "txId": tx_id, "agent": "UNASSIGNED", "name": name,
        "country": country, "flag": "🌎",
        "phone": phone, "email": f"{tg_username}@telegram" if tg_username else "",
        "tg_chat_id": tg_chat_id,
        "lastLogin": "Just now", "balance": deposit, "withdrawn": 0, "deposit": deposit,
        "status": "NEW LEAD", "retention": "NEW", "subStatus": "POTENTIAL",
        "source": "Telegram Bot",
        "comment": f"Lead captured via Telegram bot. TG: @{tg_username or 'unknown'}",
        "comments": [], "transactions": [{"id": tx_id, "date": "Just now", "type": "DEPOSIT", "asset": "Initial Capital", "amount": deposit, "profit": 0, "status": "COMPLETED"}],
        "withdrawals": [],
        "lastActivity": now
    }
    db['clients'][tx_id] = new_client
    db['timestamp'] = now
    ok = save_db(db)
    bot_log_add("intake", f"New lead captured: {name} ({country}) — ${deposit:,.0f} — {tx_id}")
    return ok, tx_id

async def handle_telegram_update(upd):
    cb = upd.get("callback_query")
    if cb:
        try:
            chat_id = cb["message"]["chat"]["id"]
            data = cb.get("data", "")
            uname = (cb.get("from") or {}).get("username", "")
            st = TG_STATE.get(chat_id)
            await tg_call("answerCallbackQuery", callback_query_id=cb["id"])
            if st and st.get("step") == "deposit" and data.startswith("dep:"):
                dep = float(data.split(":")[1])
                ok, tx_id = save_telegram_lead(st.get("name", "Unknown"), st.get("country", "Unknown"), st.get("phone", ""), dep, uname, chat_id)
                TG_STATE.pop(chat_id, None)
                if ok:
                    await tg_call("sendMessage", chat_id=chat_id, text="🎉 You're in! Your tester account is being prepared.\nA human advisor will contact you within 24 hours.\n\nMeanwhile, explore the live dashboard:\nhttps://start3ch-supervision.onrender.com/client")
                    if MANAGER_CHAT_ID:
                        await tg_call("sendMessage", chat_id=MANAGER_CHAT_ID, text=f"🚀 NEW TELEGRAM LEAD\nName: {st.get('name')}\nCountry: {st.get('country')}\nPhone: {st.get('phone') or '—'}\nDeposit: ${dep:,.0f}\nTG: @{uname or '—'}\nID: {tx_id}")
                else:
                    await tg_call("sendMessage", chat_id=chat_id, text="⚠️ Something went wrong saving your info. Please type /start and try again.")
        except Exception as e:
            print(f"Callback handling error: {e}")
        return

    msg = upd.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return
    text = (msg.get("text") or "").strip()

    if text.startswith("/start"):
        TG_STATE[chat_id] = {"step": "name"}
        bot_log_add("conversation", f"Conversation started (chat {chat_id})")
        await tg_call("sendMessage", chat_id=chat_id, text="👋 Welcome to VERUM INVEST!\nI'm the intake assistant — I'll set you up in 30 seconds.\n\n1/4 — What is your FULL NAME?")
        return
    if text.startswith("/help"):
        await tg_call("sendMessage", chat_id=chat_id, text="Type /start to begin your free tester setup.")
        return

    st = TG_STATE.get(chat_id)
    if not st:
        await tg_call("sendMessage", chat_id=chat_id, text="🤖 Type /start to begin your free tester setup.")
        return

    step = st.get("step")
    if step == "name":
        st["name"] = text; st["step"] = "country"
        await tg_call("sendMessage", chat_id=chat_id, text=f"Nice to meet you, {text} ✅\n\n2/4 — Which COUNTRY are you in?")
    elif step == "country":
        st["country"] = text; st["step"] = "phone"
        await tg_call("sendMessage", chat_id=chat_id, text="🌎 Got it.\n\n3/4 — Your PHONE or WhatsApp number?\n(type /skip if you prefer not to share)")
    elif step == "phone":
        st["phone"] = "" if text.lower() == "/skip" else text
        st["step"] = "deposit"
        kb = {"inline_keyboard": [
            [{"text": "$500 – Starter", "callback_data": "dep:500"}],
            [{"text": "$1,000 – Standard", "callback_data": "dep:1000"}],
            [{"text": "$5,000 – Professional", "callback_data": "dep:5000"}],
            [{"text": "$10,000+ – Elite", "callback_data": "dep:10000"}]
        ]}
        await tg_call("sendMessage", chat_id=chat_id, text="📞 Perfect.\n\n4/4 — What INITIAL DEPOSIT range are you considering?", reply_markup=kb)

async def telegram_poll_loop():
    offset = 0
    bot_log_add("system", "Intake bot engine started")
    while True:
        try:
            data = await tg_call("getUpdates", offset=offset, timeout=25)
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                asyncio.create_task(handle_telegram_update(upd))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Telegram poll error: {e}")
            await asyncio.sleep(3)

# ===== JARVIS ENGINE 2: AUTO FOLLOW-UP =====
async def bot_followup_loop():
    await asyncio.sleep(90)
    bot_log_add("system", "Follow-up engine started (scans every 30 min)")
    while True:
        try:
            db = load_db()
            now = time.time() * 1000
            changed = False
            for tx_id, c in (db.get("clients") or {}).items():
                if c.get("source") != "Telegram Bot" or c.get("followupSent"):
                    continue
                last = c.get("lastActivity", 0)
                age_h = (now - last) / 3600000.0
                if last and 6 < age_h < 48 and c.get("tg_chat_id"):
                    name = (c.get("name") or "friend").split(" ")[0]
                    await tg_call("sendMessage", chat_id=c["tg_chat_id"], text=f"Hey {name}! Quick check-in 🤖 — did you get a chance to open your dashboard? Your free tester slot is reserved for 24h. Any question I can answer right here?")
                    c["followupSent"] = True
                    changed = True
                    bot_log_add("followup", f"Auto follow-up sent to {c.get('name')} ({tx_id})")
            if changed:
                save_db(db)
        except Exception as e:
            print(f"Follow-up engine error: {e}")
        await asyncio.sleep(1800)

# ===== JARVIS ENGINE 3: DAILY CONTENT / BRIEFING =====
def build_briefing():
    news = get_news()
    items = (news.get("items") or [])[:5]
    lines = "\n".join(f"• {it['title']}" for it in items)
    tg_text = f"🌅 VERUM MARKET BRIEFING\n\n{lines}\n\n📊 Live charts, signals & advisor support:\nhttps://start3ch-supervision.onrender.com/client\n\n🤖 Free tester spots open — message this bot: /start"
    x_text = f"Morning market brief 🧵\n\n{lines}\n\nWe pair live algo signals with a human advisor reviewing every trade. 5 free tester spots open — reply TEST.\n\nhttps://start3ch-supervision.onrender.com/lead-capture"
    return tg_text, x_text

async def bot_content_loop():
    global LAST_BRIEF_DAY
    await asyncio.sleep(120)
    bot_log_add("system", "Content engine started (daily briefing 13:00 UTC)")
    while True:
        try:
            now = datetime.datetime.utcnow()
            if now.hour == 13 and now.minute < 5 and LAST_BRIEF_DAY != now.date().isoformat():
                LAST_BRIEF_DAY = now.date().isoformat()
                tg_text, x_text = build_briefing()
                if TELEGRAM_CHANNEL_ID:
                    r = await tg_call("sendMessage", chat_id=TELEGRAM_CHANNEL_ID, text=tg_text)
                    if r.get("ok"):
                        bot_log_add("content", "Daily briefing published to Telegram channel")
                    else:
                        bot_log_add("content", "Channel publish failed (check TELEGRAM_CHANNEL_ID)", status="error")
                else:
                    bot_log_add("content", "Briefing composed — no channel configured, skipped publish")
                queue_add({"type": "X POST", "ts": time.time() * 1000, "text": x_text})
                bot_log_add("content", "X post draft queued for human approval")
        except Exception as e:
            print(f"Content engine error: {e}")
        await asyncio.sleep(60)

# ===== JARVIS ENGINE 4: HEARTBEAT =====
async def bot_heartbeat_loop():
    while True:
        bot_log_add("system", "Heartbeat — all engines nominal")
        await asyncio.sleep(600)

def compute_stats():
    now = time.time() * 1000
    if STATS_CACHE["data"] and (now - STATS_CACHE["ts"]) < 60000:
        return STATS_CACHE["data"]
    db = load_db()
    clients = list((db.get("clients") or {}).values())
    midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    mid_ms = midnight.timestamp() * 1000
    stats = {
        "total_leads": len(clients),
        "leads_today": sum(1 for c in clients if (c.get("lastActivity") or 0) >= mid_ms),
        "telegram_leads": sum(1 for c in clients if c.get("source") == "Telegram Bot"),
        "followups_sent": sum(1 for e in BOT_LOG if e.get("type") == "followup"),
        "posts_published": sum(1 for e in BOT_LOG if e.get("type") == "content" and "published" in (e.get("message") or "").lower()),
        "conversations": sum(1 for e in BOT_LOG if e.get("type") == "conversation"),
        "pending_approvals": len(BOT_QUEUE),
        "last_heartbeat": max([e["ts"] for e in BOT_LOG if e.get("type") == "system"] or [0]),
    }
    STATS_CACHE["ts"] = now
    STATS_CACHE["data"] = stats
    return stats

@app.on_event("startup")
async def startup_event():
    if TELEGRAM_BOT_TOKEN:
        asyncio.create_task(telegram_poll_loop())
        asyncio.create_task(bot_followup_loop())
        asyncio.create_task(bot_content_loop())
        asyncio.create_task(bot_heartbeat_loop())
        bot_log_add("system", f"JARVIS online — v{APP_VERSION}")
    else:
        print("⚠️ TELEGRAM_BOT_TOKEN not set — JARVIS disabled")

# ===== JARVIS API =====
@app.get("/api/bot/log")
def bot_log_get():
    return JSONResponse(content={"status": "success", "log": list(reversed(BOT_LOG)), "queue": BOT_QUEUE, "stats": compute_stats()})

@app.post("/api/bot/queue/done")
async def bot_queue_done(request: Request):
    try:
        data = await request.json()
        idx = int(data.get("index", -1))
        if 0 <= idx < len(BOT_QUEUE):
            removed = BOT_QUEUE.pop(idx)
            _node_save("bot_queue", BOT_QUEUE)
            bot_log_add("approval", f"Approval item closed: {removed.get('type')}")
            return JSONResponse(content={"status": "success"})
        return JSONResponse(content={"status": "error", "message": "Bad index"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# ===== FIREWALL =====
@app.middleware("http")
async def strict_ip_firewall(request: Request, call_next):
    ALLOWED_IPS = ["191.96.215.107", "41.81.195.117", "127.0.0.1", "localhost", "::1"]
    ALLOWED_PREFIXES = ["196.96.", "196.97.", "105.164.", "105.161.", "105.166.", "41.81.", "41.82."]
    path = request.url.path
    
    public_routes = ["/client", "/client-login", "/health", "/favicon.ico", "/static", "/docs", "/openapi.json", "/api/db", "/api/db/update", "/api/leads/submit", "/lead-capture", "/api/news"]
    if any(path == route or path.startswith(route + "/") for route in public_routes):
        return await call_next(request)
    
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    real_ip_header = request.headers.get("X-Real-IP", "")
    client_host = request.client.host if request.client else "unknown"
    
    if forwarded_for: detected_ip = forwarded_for.split(",")[0].strip()
    elif real_ip_header: detected_ip = real_ip_header.strip()
    else: detected_ip = client_host

    if detected_ip in ["127.0.0.1", "localhost", "::1"]: return await call_next(request)

    allowed = (detected_ip in ALLOWED_IPS) or any(detected_ip.startswith(p) for p in ALLOWED_PREFIXES)

    if not allowed:
        return HTMLResponse(
            content="""<!DOCTYPE html><html><head><style>body{background:#02040a;color:#ef4444;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}.box{text-align:center;padding:40px;border:2px solid #ef4444;border-radius:8px;background:rgba(239,68,68,0.05);}</style></head><body><div class="box"><h1>403 ACCESS DENIED</h1><p>IP: """ + detected_ip + """</p></div></body></html>""",
            status_code=403
        )
    return await call_next(request)

# ===== NEWS =====
@app.get("/api/news")
def get_news():
    now = time.time()
    if NEWS_CACHE["items"] and (now - NEWS_CACHE["ts"]) < 300:
        return JSONResponse(content={"status": "success", "items": NEWS_CACHE["items"], "cached": True})
    items = []
    for source, url in NEWS_FEEDS:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            root = ET.fromstring(r.content)
            count = 0
            for item in root.iter('item'):
                if count >= 12:
                    break
                title = htmllib.escape(_strip_tags(item.findtext('title')))
                link = (item.findtext('link') or '').strip()
                pub = (item.findtext('pubDate') or '').strip()
                desc = htmllib.escape(_strip_tags(item.findtext('description'))[:200])
                if title:
                    items.append({"source": source, "title": title, "link": link, "pubDate": pub, "description": desc})
                    count += 1
        except Exception as e:
            print(f"News feed error ({source}): {e}")
    items.sort(key=lambda x: _parse_dt(x["pubDate"]), reverse=True)
    items = items[:40]
    if items:
        NEWS_CACHE["ts"] = now
        NEWS_CACHE["items"] = items
    return JSONResponse(content={"status": "success", "items": items, "cached": False})

# ===== CORE API =====
@app.get("/api/db")
def get_database(): 
    db = load_db()
    return JSONResponse(content=db)

@app.post("/api/agents/update")
async def update_agents(request: Request):
    try:
        data = await request.json()
        action = data.get('action', 'add')
        name = (data.get('name') or '').strip().upper()
        if not name:
            return JSONResponse(content={"status": "error", "message": "No agent name provided"}, status_code=400)
        db = load_db()
        agents = db.get('agents', [])
        if action == 'add':
            if name not in agents:
                agents.append(name)
                print(f"➕ Agent added server-side: {name}")
        elif action == 'remove':
            if name in agents and name != 'ALL':
                agents.remove(name)
                print(f"➖ Agent removed server-side: {name}")
        db['agents'] = agents
        db['timestamp'] = time.time() * 1000
        if save_db(db):
            return JSONResponse(content={"status": "success", "agents": agents})
        return JSONResponse(content={"status": "error", "message": "Firebase rejected the save"}, status_code=500)
    except Exception as e:
        print(f"❌ Agent update error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/db/update")
async def update_database(request: Request):
    try:
        data = await request.json()
        incoming_clients = data.get('clients', {})
        current_db = load_db()
        current_clients = current_db.get('clients', {})
        updated_count = 0
        ignored_count = 0
        for tx_id, incoming_data in incoming_clients.items():
            incoming_activity = incoming_data.get('lastActivity', 0)
            if tx_id not in current_clients:
                current_clients[tx_id] = incoming_data
                updated_count += 1
            else:
                existing_data = current_clients[tx_id]
                existing_activity = existing_data.get('lastActivity', 0)
                if incoming_activity > existing_activity:
                    existing_data['status'] = incoming_data.get('status', existing_data['status'])
                    existing_data['retention'] = incoming_data.get('retention', existing_data['retention'])
                    existing_data['subStatus'] = incoming_data.get('subStatus', existing_data['subStatus'])
                    existing_data['agent'] = incoming_data.get('agent', existing_data['agent'])
                    existing_data['lastActivity'] = incoming_activity
                    inc_comments = incoming_data.get('comments', [])
                    exist_comments = existing_data.get('comments', [])
                    existing_keys = {c.get('text', '') + c.get('time', '') for c in exist_comments}
                    for inc_c in inc_comments:
                        key = inc_c.get('text', '') + inc_c.get('time', '')
                        if key not in existing_keys:
                            exist_comments.append(inc_c)
                            existing_keys.add(key)
                    exist_comments.sort(key=lambda x: x.get('time', ''), reverse=True)
                    existing_data['comments'] = exist_comments
                    current_clients[tx_id] = existing_data
                    updated_count += 1
                else:
                    ignored_count += 1
        current_db['clients'] = current_clients
        current_db['timestamp'] = time.time() * 1000
        success = save_db(current_db)
        print(f"✅ Sync Complete. v{APP_VERSION} | Clients updated: {updated_count}, ignored: {ignored_count}")
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
        now = time.time() * 1000
        new_client = {
            "txId": tx_id, "agent": "UNASSIGNED", "name": data.get('name', 'Unknown'),
            "country": data.get('country', 'Unknown'), "flag": "🌎",
            "phone": data.get('phone', ''), "email": data.get('email', ''),
            "lastLogin": "Just now", "balance": 0, "withdrawn": 0, "deposit": 0,
            "status": "NEW LEAD", "retention": "NEW", "subStatus": "POTENTIAL",
            "source": data.get('source', 'Website Landing Page'),
            "comment": "New lead injected.", "comments": [],
            "transactions": [{"id": tx_id, "date": "Just now", "type": "DEPOSIT", "asset": "Initial Capital", "amount": 0, "profit": 0, "status": "COMPLETED"}],
            "withdrawals": [],
            "lastActivity": now
        }
        db['clients'][tx_id] = new_client
        db['timestamp'] = now
        success = save_db(db)
        if success:
            return JSONResponse(content={"status": "success", "message": "Lead captured successfully."})
        else:
            return JSONResponse(content={"status": "error", "message": "Failed to save lead."}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# ===== PAGES =====
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
@app.get("/bot-control", response_class=HTMLResponse)
def read_bot_control(): return HTMLResponse(content=(BASE_DIR / "botcontrol.html").read_text(encoding="utf-8"))
@app.get("/health")
def health_check(): return {"status": "online", "system": "Verum Invest Mainframe", "version": APP_VERSION, "telegram_bot": bool(TELEGRAM_BOT_TOKEN)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)