"""
Odoo MCP Server - Exposes Odoo accounting tools to Claude Code via MCP protocol
Uses Odoo's JSON-RPC API for invoices, payments, partners, and reporting.

Prerequisites:
    uv add mcp python-dotenv
    Odoo Community running locally (http://localhost:8069)
    .env with ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD

Usage:
    uv run python .claude/skills/odoo-integration/scripts/odoo_mcp_server.py
"""

import os
import json
import random
import logging
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OdooMCP")

mcp = FastMCP("Odoo MCP Server")

# Odoo connection settings
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "ai_employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    reply = json.loads(urllib.request.urlopen(req).read().decode("UTF-8"))
    if reply.get("error"):
        raise Exception(reply["error"])
    return reply["result"]


def odoo_call(service, method, *args):
    return json_rpc(f"{ODOO_URL}/jsonrpc", "call", {
        "service": service, "method": method, "args": args
    })


def authenticate():
    uid = odoo_call("common", "login", ODOO_DB, ODOO_USER, ODOO_PASSWORD)
    if not uid:
        raise Exception("Odoo authentication failed")
    return uid


def execute(uid, model, method, *args, **kwargs):
    return odoo_call("object", "execute_kw", ODOO_DB, uid, ODOO_PASSWORD, model, method, list(args), kwargs)


@mcp.tool()
def odoo_test_connection() -> str:
    """Test connection to Odoo ERP. Returns authentication status."""
    try:
        uid = authenticate()
        return f"Odoo connection successful! Authenticated as UID: {uid}"
    except Exception as e:
        return f"Odoo connection failed: {str(e)}"


@mcp.tool()
def odoo_list_invoices(limit: int = 20) -> str:
    """List invoices from Odoo. Returns invoice details (name, partner, amount, status)."""
    try:
        uid = authenticate()
        invoices = execute(
            uid, "account.move", "search_read",
            [["move_type", "in", ["out_invoice", "in_invoice"]]],
            fields=["name", "partner_id", "amount_total", "state", "invoice_date", "move_type"],
            limit=limit,
        )
        if not invoices:
            return "No invoices found in Odoo."
        return json.dumps(invoices, indent=2, default=str)
    except Exception as e:
        return f"Error listing invoices: {str(e)}"


@mcp.tool()
def odoo_create_invoice(partner_name: str, product_description: str, quantity: float, unit_price: float) -> str:
    """Create a draft invoice in Odoo. REQUIRES HUMAN APPROVAL before confirming.

    Args:
        partner_name: Customer/vendor name to search for
        product_description: Description of the product/service
        quantity: Quantity of items
        unit_price: Price per unit
    """
    try:
        uid = authenticate()
        # Search for partner
        partners = execute(uid, "res.partner", "search_read",
                          [["name", "ilike", partner_name]],
                          fields=["id", "name"], limit=1)
        if not partners:
            return f"Partner '{partner_name}' not found in Odoo. Please create the partner first."

        partner_id = partners[0]["id"]
        invoice_id = execute(uid, "account.move", "create", {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_line_ids": [(0, 0, {
                "name": product_description,
                "quantity": quantity,
                "price_unit": unit_price,
            })],
        })
        return f"Draft invoice created (ID: {invoice_id}) for {partners[0]['name']}. Amount: {quantity * unit_price}. Status: DRAFT — requires approval to confirm."
    except Exception as e:
        return f"Error creating invoice: {str(e)}"


@mcp.tool()
def odoo_search_partners(name: str = "", limit: int = 10) -> str:
    """Search for partners (customers/vendors) in Odoo.

    Args:
        name: Name to search for (partial match). Leave empty for all.
        limit: Maximum results to return.
    """
    try:
        uid = authenticate()
        domain = [["name", "ilike", name]] if name else []
        partners = execute(uid, "res.partner", "search_read", domain,
                          fields=["name", "email", "phone", "is_company"],
                          limit=limit)
        if not partners:
            return "No partners found."
        return json.dumps(partners, indent=2, default=str)
    except Exception as e:
        return f"Error searching partners: {str(e)}"


@mcp.tool()
def odoo_get_balance() -> str:
    """Get account balances from Odoo. Returns all chart of accounts with current balances."""
    try:
        uid = authenticate()
        accounts = execute(uid, "account.account", "search_read", [],
                          fields=["name", "code", "current_balance"],
                          limit=50)
        if not accounts:
            return "No accounts found."
        # Filter accounts with non-zero balance
        summary = []
        for acc in accounts:
            summary.append(f"  {acc['code']} - {acc['name']}: {acc.get('current_balance', 0)}")
        return "Account Balances:\n" + "\n".join(summary)
    except Exception as e:
        return f"Error getting balance: {str(e)}"


@mcp.tool()
def odoo_get_payments(limit: int = 20) -> str:
    """List recent payments from Odoo."""
    try:
        uid = authenticate()
        payments = execute(uid, "account.payment", "search_read", [],
                          fields=["name", "partner_id", "amount", "payment_type", "state", "date"],
                          limit=limit)
        if not payments:
            return "No payments found."
        return json.dumps(payments, indent=2, default=str)
    except Exception as e:
        return f"Error listing payments: {str(e)}"


@mcp.tool()
def odoo_weekly_audit() -> str:
    """Generate a weekly accounting audit summary from Odoo.
    Includes invoice counts, total revenue, outstanding payments, and account balances."""
    try:
        uid = authenticate()

        # Get invoices
        invoices = execute(uid, "account.move", "search_read",
                          [["move_type", "in", ["out_invoice", "in_invoice"]]],
                          fields=["name", "amount_total", "state", "move_type", "amount_residual"])

        # Get payments
        payments = execute(uid, "account.payment", "search_read", [],
                          fields=["amount", "payment_type", "state"])

        # Calculate metrics
        total_invoiced = sum(i["amount_total"] for i in invoices if i["move_type"] == "out_invoice")
        total_outstanding = sum(i["amount_residual"] for i in invoices if i["state"] == "posted")
        total_paid = sum(p["amount"] for p in payments if p["state"] == "posted" and p["payment_type"] == "inbound")

        audit = f"""Weekly Accounting Audit
Generated: {datetime.now().isoformat()}

Invoices: {len(invoices)} total
  - Total Invoiced: ${total_invoiced:,.2f}
  - Outstanding: ${total_outstanding:,.2f}
  - Draft: {sum(1 for i in invoices if i['state'] == 'draft')}
  - Posted: {sum(1 for i in invoices if i['state'] == 'posted')}

Payments: {len(payments)} total
  - Total Received: ${total_paid:,.2f}

Status: {'Healthy' if total_outstanding < total_invoiced * 0.5 else 'Attention needed - high outstanding'}"""

        return audit
    except Exception as e:
        return f"Error generating audit: {str(e)}"


if __name__ == "__main__":
    mcp.run()
