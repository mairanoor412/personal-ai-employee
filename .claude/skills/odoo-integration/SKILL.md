# Odoo Integration Skill

## Description
Integrates with Odoo Community ERP via JSON-RPC/XML-RPC for accounting operations — invoices, payments, and financial reporting.

## When to Use
- User asks to "create invoice", "check payments", "get accounting data"
- Reasoning loop needs to record financial transactions
- CEO briefing needs financial data from Odoo

## Instructions

### Connection Setup
Requires `.env` variables:
```
ODOO_URL=http://localhost:8069
ODOO_DB=your_database
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### Available Operations
1. **Authenticate** — Login and get user ID
2. **Create Invoice** — Create customer/vendor invoices
3. **Read Invoices** — List and filter invoices
4. **Create Payment** — Record payments
5. **Get Account Balance** — Read account balances
6. **Search Partners** — Find customers/vendors

### JSON-RPC Pattern
```python
import json, urllib.request

def json_rpc(url, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    req = urllib.request.Request(url=url, data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"})
    reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
    return reply["result"]

def call(url, service, method, *args):
    return json_rpc(url, "call", {"service": service, "method": method, "args": args})
```

### Approval Rules
- Creating invoices > $100 → requires human approval
- Recording payments → always requires approval
- Reading data → no approval needed

### Output
- Save financial summaries to `AI_Employee_Vault/Accounting/`
- Log all operations to `AI_Employee_Vault/Logs/`

### Helper Script
Run: `uv run python .claude/skills/odoo-integration/scripts/odoo_client.py`
