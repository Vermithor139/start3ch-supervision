from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verum ECN | Global Terminal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #090d16;
            --bg-sidebar: #05080e;
            --bg-card: #0f172a;
            --bg-hover: #1e293b;
            --accent-blue: #3b82f6;
            --accent-blue-hover: #2563eb;
            --accent-green: #22c55e;
            --accent-amber: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #1e293b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-primary); color: var(--text-main); display: flex; min-height: 100vh; }

        /* Sidebar Navigation */
        .sidebar { width: 260px; background: var(--bg-sidebar); border-right: 1px solid var(--border-color); padding: 24px 16px; display: flex; flex-direction: column; justify-content: space-between; }
        .brand-container { display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px; padding: 0 8px; }
        .brand { font-size: 1.15rem; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px; letter-spacing: 0.05em; }
        .brand span { color: var(--accent-blue); font-size: 0.75rem; background: rgba(59, 130, 246, 0.15); padding: 2px 6px; border-radius: 4px; }
        .latency-badge { font-size: 0.7rem; font-weight: 600; color: var(--accent-green); background: rgba(34, 197, 94, 0.12); padding: 4px 8px; border-radius: 12px; display: flex; align-items: center; gap: 4px; }
        .latency-badge::before { content: ''; width: 6px; height: 6px; background: var(--accent-green); border-radius: 50%; }

        .nav-category { font-size: 0.7rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; padding: 0 12px 8px; margin-top: 8px; }
        .nav-list { list-style: none; display: flex; flex-direction: column; gap: 4px; margin-bottom: 24px; }
        .nav-item a { display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: var(--text-muted); text-decoration: none; border-radius: 8px; font-size: 0.875rem; font-weight: 500; transition: all 0.2s ease; }
        .nav-item.active a, .nav-item a:hover { background: var(--bg-hover); color: var(--text-main); }

        .user-profile { display: flex; align-items: center; gap: 12px; padding: 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; }
        .user-avatar { width: 32px; height: 32px; background: var(--accent-blue); color: #fff; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; justify-content: center; border-radius: 6px; }
        .user-info { font-size: 0.8rem; }
        .user-name { font-weight: 600; color: var(--text-main); }
        .user-role { color: var(--accent-green); font-size: 0.7rem; margin-top: 2px; }

        /* Main Content Area */
        .main-content { flex: 1; padding: 32px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .header-title h1 { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.01em; }
        .header-title p { color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; }
        
        .header-actions { display: flex; gap: 12px; }

        /* Modern Buttons */
        .btn { background: var(--accent-blue); color: #fff; border: none; padding: 9px 16px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background: var(--accent-blue-hover); transform: translateY(-1px); }
        .btn-outline { background: transparent; border: 1px solid var(--border-color); color: var(--text-main); }
        .btn-outline:hover { background: var(--bg-hover); border-color: var(--text-muted); }

        /* Terminal Card Container */
        .terminal-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 28px; max-width: 760px; }
        .terminal-card h2 { font-size: 1rem; font-weight: 600; margin-bottom: 6px; }
        .terminal-card p { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 24px; }

        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
        .form-input { width: 100%; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px; color: var(--text-main); font-family: 'Inter', sans-serif; font-size: 0.9rem; transition: border-color 0.2s; }
        .form-input:focus { outline: none; border-color: var(--accent-blue); }

        .toast { margin-top: 16px; font-size: 0.85rem; color: var(--accent-green); display: none; align-items: center; gap: 6px; }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <div class="sidebar">
        <div>
            <div class="brand-container">
                <div class="brand">VERUM <span>ECN</span></div>
                <div class="latency-badge">12ms</div>
            </div>
            
            <div class="nav-category">Navigation Hub</div>
            <ul class="nav-list">
                <li class="nav-item"><a href="#">📊 Market Overview</a></li>
                <li class="nav-item"><a href="#">👥 Client Accounts</a></li>
                <li class="nav-item"><a href="#">📜 Order Execution Log</a></li>
                <li class="nav-item"><a href="#">📈 Advanced Analytics</a></li>
                <li class="nav-item active"><a href="#">⚙️ Terminal Settings</a></li>
            </ul>
        </div>

        <div class="user-profile">
            <div class="user-avatar">JS</div>
            <div class="user-info">
                <div class="user-name">Julian Sterling</div>
                <div class="user-role">MT5 #849201-LIVE</div>
            </div>
        </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
        <div class="header">
            <div class="header-title">
                <h1>TERMINAL SETTINGS</h1>
                <p>Configure broker gateway bridging and execution latency rules.</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-outline" onclick="alert('Exporting statement CSV...')">Export CSV</button>
                <button class="btn" onclick="alert('Opening position ticket...')">+ New Position</button>
            </div>
        </div>

        <!-- Terminal Parameters Card -->
        <div class="terminal-card">
            <h2>MT5 TERMINAL PARAMETERS</h2>
            <p>Configure gateway bridging and execution latency rules.</p>
            
            <div class="form-group">
                <label class="form-label">Broker Gateway ID</label>
                <input type="text" class="form-input" id="gatewayId" value="VERUM-STP-ECN-01">
            </div>

            <div class="form-group">
                <label class="form-label">Liquidity Provider Webhook</label>
                <input type="text" class="form-input" id="webhookUrl" value="https://feed.verum.financial/v1/mt5-bridge">
            </div>

            <button class="btn" onclick="saveConfig()">Save Terminal Config</button>
            <div id="successToast" class="toast">✓ Configuration successfully updated and synced across ECN nodes.</div>
        </div>
    </div>

    <script>
        function saveConfig() {
            const btn = document.querySelector('.terminal-card .btn');
            const toast = document.getElementById('successToast');
            btn.textContent = 'Saving...';
            setTimeout(() => {
                btn.textContent = 'Save Terminal Config';
                toast.style.display = 'flex';
                setTimeout(() => {
                    toast.style.display = 'none';
                }, 4000);
            }, 600);
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT