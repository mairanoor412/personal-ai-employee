"""
Odoo Client - JSON-RPC integration for accounting operations
Connects to Odoo Community ERP for invoices, payments, and reporting.

Prerequisites:
    Odoo Community running locally or remotely
    .env with ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD

Usage:
    uv run python .claude/skills/odoo-integration/scripts/odoo_client.py --action list_invoices
"""

import os
import json
import random
import logging
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("OdooClient")


class OdooClient:
    def __init__(self, vault_path: str = "./AI_Employee_Vault"):
        self.url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = os.getenv("ODOO_DB", "odoo")
        self.user = os.getenv("ODOO_USER", "admin")
        self.password = os.getenv("ODOO_PASSWORD", "admin")
        self.vault_path = Path(vault_path)
        self.accounting_dir = self.vault_path / "Accounting"
        self.logs_dir = self.vault_path / "Logs"
        self.uid = None

    def json_rpc(self, url, method, params):
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

    def call(self, service, method, *args):
        url = f"{self.url}/jsonrpc"
        return self.json_rpc(url, "call", {"service": service, "method": method, "args": args})

    def authenticate(self):
        self.uid = self.call("common", "login", self.db, self.user, self.password)
        if self.uid:
            logger.info(f"Authenticated as UID: {self.uid}")
        else:
            logger.error("Authentication failed")
        return self.uid

    def execute(self, model, method, *args, **kwargs):
        if not self.uid:
            self.authenticate()
        return self.call("object", "execute_kw", self.db, self.uid, self.password, model, method, list(args), kwargs)

    def list_invoices(self, limit=20):
        invoices = self.execute(
            "account.move", "search_read",
            [["move_type", "in", ["out_invoice", "in_invoice"]]],
            fields=["name", "partner_id", "amount_total", "state", "invoice_date", "move_type"],
            limit=limit,
        )
        logger.info(f"Found {len(invoices)} invoices")
        return invoices

    def create_invoice(self, partner_id, lines, invoice_type="out_invoice"):
        invoice_id = self.execute("account.move", "create", {
            "move_type": invoice_type,
            "partner_id": partner_id,
            "invoice_line_ids": [(0, 0, line) for line in lines],
        })
        logger.info(f"Created invoice ID: {invoice_id}")
        return invoice_id

    def search_partners(self, name="", limit=10):
        partners = self.execute(
            "res.partner", "search_read",
            [["name", "ilike", name]] if name else [],
            fields=["name", "email", "phone"],
            limit=limit,
        )
        return partners

    def get_account_balance(self):
        accounts = self.execute(
            "account.account", "search_read",
            [],
            fields=["name", "code", "current_balance"],
            limit=50,
        )
        return accounts

    def save_report(self, data, report_name):
        filepath = self.accounting_dir / f"{report_name}_{datetime.now().strftime('%Y%m%d')}.md"
        content = f"# {report_name}\n\nGenerated: {datetime.now().isoformat()}\n\n"
        content += "```json\n" + json.dumps(data, indent=2, default=str) + "\n```\n"
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Report saved: {filepath.name}")
        return filepath

    def log_action(self, action, details):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": f"odoo_{action}",
            "actor": "odoo_client",
            "details": details,
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Odoo Client for AI Employee")
    parser.add_argument("--action", choices=["list_invoices", "search_partners", "balance", "test"],
                        default="test", help="Action to perform")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    args = parser.parse_args()

    client = OdooClient(vault_path=args.vault)

    if args.action == "test":
        uid = client.authenticate()
        if uid:
            logger.info("Odoo connection successful!")
        else:
            logger.error("Odoo connection failed!")
    elif args.action == "list_invoices":
        client.authenticate()
        invoices = client.list_invoices()
        client.save_report(invoices, "Invoice_Report")
    elif args.action == "search_partners":
        client.authenticate()
        partners = client.search_partners()
        client.save_report(partners, "Partner_Report")
    elif args.action == "balance":
        client.authenticate()
        accounts = client.get_account_balance()
        client.save_report(accounts, "Account_Balance")


if __name__ == "__main__":
    main()
