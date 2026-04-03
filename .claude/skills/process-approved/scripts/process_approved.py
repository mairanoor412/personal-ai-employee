"""
Process Approved - Watches /Approved/ folder and executes approved actions automatically.
Routes to correct executor based on file type (Odoo invoice, social post, WhatsApp reply, etc.)

Prerequisites:
    uv add watchdog python-dotenv

Usage:
    uv run python .claude/skills/process-approved/scripts/process_approved.py --vault ./AI_Employee_Vault
"""

import os
import json
import time
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
logger = logging.getLogger("ProcessApproved")


class ApprovedProcessor:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        self.needs_action_dir = self.vault_path / "Needs_Action"

        # Odoo settings
        self.odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.odoo_db = os.getenv("ODOO_DB", "ai_employee")
        self.odoo_user = os.getenv("ODOO_USER", "admin")
        self.odoo_password = os.getenv("ODOO_PASSWORD", "admin")

    def parse_frontmatter(self, filepath: Path) -> dict:
        content = filepath.read_text(encoding="utf-8")
        metadata = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        metadata[key.strip()] = val.strip()
                metadata["_body"] = parts[2].strip()
        return metadata

    # ── Odoo JSON-RPC helpers ──
    def odoo_rpc(self, service, method, *args):
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": random.randint(0, 1000000000),
        }
        req = urllib.request.Request(
            url=f"{self.odoo_url}/jsonrpc",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        reply = json.loads(urllib.request.urlopen(req).read().decode("UTF-8"))
        if reply.get("error"):
            raise Exception(reply["error"])
        return reply["result"]

    def odoo_authenticate(self):
        uid = self.odoo_rpc("common", "login", self.odoo_db, self.odoo_user, self.odoo_password)
        if not uid:
            raise Exception("Odoo authentication failed")
        return uid

    def odoo_execute(self, uid, model, method, *args, **kwargs):
        return self.odoo_rpc("object", "execute_kw", self.odoo_db, uid, self.odoo_password, model, method, list(args), kwargs)

    # ── Action Handlers ──
    def handle_odoo_invoice(self, metadata: dict, filepath: Path) -> bool:
        """Create invoice in Odoo from approved file."""
        try:
            uid = self.odoo_authenticate()
            partner_id = int(metadata.get("partner_id", 0))
            partner_name = metadata.get("partner_name", "")

            if not partner_id and partner_name:
                partners = self.odoo_execute(uid, "res.partner", "search_read",
                                            [["name", "ilike", partner_name]],
                                            fields=["id", "name"], limit=1)
                if partners:
                    partner_id = partners[0]["id"]

            if not partner_id:
                logger.error(f"Partner not found: {partner_name}")
                return False

            # Parse body for invoice details
            body = metadata.get("_body", "")
            description = "Service"
            quantity = 1
            price = 0

            for line in body.split("\n"):
                if "Description" in line and ":" in line:
                    description = line.split(":", 1)[1].strip().strip("*")
                elif "Quantity" in line and ":" in line:
                    try:
                        quantity = float(line.split(":", 1)[1].strip().strip("*"))
                    except ValueError:
                        pass
                elif "Unit Price" in line and ":" in line:
                    try:
                        price_str = line.split(":", 1)[1].strip().strip("*").replace("$", "").replace(",", "")
                        price = float(price_str)
                    except ValueError:
                        pass

            invoice_id = self.odoo_execute(uid, "account.move", "create", {
                "move_type": "out_invoice",
                "partner_id": partner_id,
                "invoice_line_ids": [(0, 0, {
                    "name": description,
                    "quantity": quantity,
                    "price_unit": price,
                })],
            })
            logger.info(f"Invoice created in Odoo! ID: {invoice_id}, Partner: {partner_name}, Amount: ${quantity * price:,.2f}")
            return True
        except Exception as e:
            logger.error(f"Odoo invoice creation failed: {e}")
            return False

    def detect_file_type(self, filename: str, metadata: dict) -> str:
        """Detect action type from filename and metadata."""
        fname = filename.upper()
        if "ODOO" in fname or metadata.get("type") == "odoo_invoice":
            return "odoo_invoice"
        elif "FACEBOOK" in fname or metadata.get("type") == "facebook_post":
            return "facebook_post"
        elif "INSTAGRAM" in fname or metadata.get("type") == "instagram_post":
            return "instagram_post"
        elif "LINKEDIN" in fname or metadata.get("type") == "linkedin_post":
            return "linkedin_post"
        elif "TWITTER" in fname or metadata.get("type") == "twitter_post":
            return "twitter_post"
        elif "WHATSAPP_REPLY" in fname or metadata.get("type") == "whatsapp_reply":
            return "whatsapp_reply"
        elif "EMAIL" in fname or metadata.get("action") == "email_send":
            return "email_send"
        return "unknown"

    def process_file(self, filepath: Path) -> bool:
        """Process a single approved file."""
        logger.info(f"Processing: {filepath.name}")
        metadata = self.parse_frontmatter(filepath)
        file_type = self.detect_file_type(filepath.name, metadata)
        logger.info(f"  Type: {file_type}")

        success = False

        if file_type == "odoo_invoice":
            success = self.handle_odoo_invoice(metadata, filepath)
        elif file_type in ("facebook_post", "instagram_post", "linkedin_post", "twitter_post"):
            # Social media posts are handled by their own scripts
            logger.info(f"  Social post — run the {file_type} script to publish")
            logger.info(f"  Skipping (handled by dedicated poster script)")
            return False
        elif file_type == "whatsapp_reply":
            logger.info("  WhatsApp reply — run whatsapp_reply.py to send")
            return False
        elif file_type == "email_send":
            logger.info("  Email — run email MCP server to send")
            return False
        else:
            logger.warning(f"  Unknown file type: {filepath.name}")
            return False

        if success:
            # Move to Done
            src = self.approved_dir / filepath.name
            dest = self.done_dir / filepath.name
            try:
                if src.exists():
                    src.rename(dest)
                    logger.info(f"  Moved to Done/")
                else:
                    logger.warning(f"  File already moved or deleted: {src}")
            except Exception as move_err:
                logger.warning(f"  Move failed: {move_err}")
            self.log_action(filepath.name, file_type, "completed")
        else:
            self.log_action(filepath.name, file_type, "failed")

        return success

    def scan_and_process(self):
        """Scan /Approved/ folder and process all files."""
        files = list(self.approved_dir.glob("*.md"))
        if not files:
            logger.info("No approved files to process.")
            return

        logger.info(f"Found {len(files)} approved file(s)")
        for filepath in files:
            self.process_file(filepath)

    def watch(self, interval: int = 10):
        """Continuously watch /Approved/ folder for new files."""
        logger.info(f"Watching /Approved/ folder every {interval}s...")
        logger.info("Press Ctrl+C to stop")
        processed = set()

        while True:
            try:
                files = list(self.approved_dir.glob("*.md"))
                for filepath in files:
                    if filepath.name not in processed:
                        success = self.process_file(filepath)
                        if success:
                            processed.add(filepath.name)
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Watcher stopped.")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(interval)

    def log_action(self, filename: str, action_type: str, result: str):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": f"process_approved_{action_type}",
            "actor": "process_approved",
            "file": filename,
            "result": result,
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
    parser = argparse.ArgumentParser(description="Process Approved Actions for AI Employee")
    parser.add_argument("--vault", default="./AI_Employee_Vault", help="Path to vault")
    parser.add_argument("--watch", action="store_true", help="Continuously watch for new approved files")
    parser.add_argument("--interval", type=int, default=10, help="Watch interval in seconds")
    args = parser.parse_args()

    processor = ApprovedProcessor(vault_path=args.vault)

    if args.watch:
        processor.watch(interval=args.interval)
    else:
        processor.scan_and_process()


if __name__ == "__main__":
    main()
