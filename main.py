from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial CRM | Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --bg-hover: #334155;
            --accent-blue: #38bdf8;
            --accent-green: #22c55e;
            --accent-amber: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-primary); color: var(--text-main); display: flex; min-height: 100vh; }

        /* Sidebar Navigation */
        .sidebar { width: 260px; background: #090d16; border-right: 1px solid var(--border-color); padding: 24px 16px; display: flex; flex-direction: column; justify-content: space-between; }
        .brand { font-size: 1.25rem; font-weight: 700; color: var(--accent-blue); display: flex; align-items: center; gap: 10px; margin-bottom: 32px; padding: 0 8px; }
        .nav-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }
        .nav-item a { display: flex; align-items: center; gap: 12px; padding: 12px 14px; color: var(--text-muted); text-decoration: none; border-radius: 8px; font-weight: 500; transition: all 0.2s ease; }
        .nav-item.active a, .nav-item a:hover { background: var(--bg-card); color: var(--text-main); }

        /* Main Content Container */
        .main-content { flex: 1; padding: 32px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .header h1 { font-size: 1.75rem; font-weight: 700; }
        .header p { color: var(--text-muted); font-size: 0.9rem; margin-top: 4px; }

        /* Modern Action Buttons */
        .btn { background: var(--accent-blue); color: #0f172a; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: transform 0.15s ease, opacity 0.2s ease; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn-outline { background: transparent; border: 1px solid var(--border-color); color: var(--text-main); }
        .btn-outline:hover { background: var(--bg-card); }

        /* Metric Grid Cards */
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 32px; }
        .metric-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; position: relative; }
        .metric-title { color: var(--text-muted); font-size: 0.85rem; font-weight: 500; margin-bottom: 8px; }
        .metric-value { font-size: 1.8rem; font-weight: 700; color: var(--text-main); }
        .metric-badge { position: absolute; top: 20px; right: 20px; font-size: 0.75rem; font-weight: 600; padding: 4px 8px; border-radius: 20px; }
        .badge-green { background: rgba(34, 197, 94, 0.15); color: var(--accent-green); }
        .badge-amber { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }

        /* Modern Data Table */
        .table-container { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
        .table-header { padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
        .table-header h2 { font-size: 1.1rem; font-weight: 600; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: #162032; color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 14px 20px; font-weight: 600; }
        td { padding: 16px 20px; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: var(--bg-hover); }

        /* Status Pills */
        .status-pill { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
        .status-paid { background: rgba(34, 197, 94, 0.15); color: var(--accent-green); }
        .status-pending { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <div class="sidebar">
        <div>
            <div class="brand">⚡ Financial CRM</div>
            <ul class="nav-list">
                <li class="nav-item active"><a href="#">📊 Dashboard</a></li>
                <li class="nav-item"><a href="#">👥 Clients</a></li>
                <li class="nav-item"><a href="#">💳 Transactions</a></li>
                <li class="nav-item"><a href="#">📈 Analytics</a></li>
                <li class="nav-item"><a href="#">⚙️ Settings</a></li>
            </ul>
        </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
        <div class="header">
            <div>
                <h1>Financial Dashboard</h1>
                <p>Welcome back! Here is your real-time portfolio summary.</p>
            </div>
            <div style="display: flex; gap: 12px;">
                <button class="btn btn-outline" onclick="alert('Exporting statement...')">Export CSV</button>
                <button class="btn" onclick="addNewTransaction()">+ Add Transaction</button>
            </div>
        </div>

        <!-- Metric Grid -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Total Active Clients</div>
                <div class="metric-value">3</div>
                <span class="metric-badge badge-green">+1 this month</span>
            </div>
            <div class="metric-card">
                <div class="metric-title">Monthly Revenue</div>
                <div class="metric-value">$24,500</div>
                <span class="metric-badge badge-green">+12.5%</span>
            </div>
            <div class="metric-card">
                <div class="metric-title">Pending Invoices</div>
                <div class="metric-value">$12,500</div>
                <span class="metric-badge badge-amber">2 Outstanding</span>
            </div>
        </div>

        <!-- Interactive Table -->
        <div class="table-container">
            <div class="table-header">
                <h2>Recent Financial Activity</h2>
            </div>
            <table id="transactionsTable">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Acme Corp</strong></td>
                        <td>$8,200.00</td>
                        <td><span class="status-pill status-paid">Paid</span></td>
                        <td>2026-10-18</td>
                    </tr>
                    <tr>
                        <td><strong>Apex Industries</strong></td>
                        <td>$12,500.00</td>
                        <td><span class="status-pill status-pending">Pending</span></td>
                        <td>2026-10-19</td>
                    </tr>
                    <tr>
                        <td><strong>Global Logistics</strong></td>
                        <td>$3,800.00</td>
                        <td><span class="status-pill status-paid">Paid</span></td>
                        <td>2026-10-20</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function addNewTransaction() {
            const client = prompt("Enter Client Name:", "Vortex Systems");
            const amount = prompt("Enter Amount ($):", "5,400");
            if (client && amount) {
                const table = document.getElementById("transactionsTable").getElementsByTagName('tbody')[0];
                const newRow = table.insertRow(0);
                const today = new Date().toISOString().split('T')[0];
                newRow.innerHTML = `<td><strong>${client}</strong></td><td>$${amount}.00</td><td><span class="status-pill status-pending">Pending</span></td><td>${today}</td>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT
