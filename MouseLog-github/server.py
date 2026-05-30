#!/usr/bin/env python3
"""
MouseLog — Local Server v3
Run:  python3 server.py
Open: http://localhost:8888
Data: mouselog_data.json (same folder)
"""

import json, os, uuid, shutil
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DATA_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mouselog_data.json")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
PORT       = 8888

# ── data ──────────────────────────────────────────────────────────────────────

def migrate_gene_format(raw):
    """Convert old single-value genes {gene: "+"} → new {gene: {tg,wt}} format."""
    if not raw or not isinstance(raw, dict):
        return {}
    out = {}
    for k, v in raw.items():
        if isinstance(v, dict) and ("tg" in v or "wt" in v):
            out[k] = v  # already new format
        else:
            s = str(v or "?")
            if   s == "+":   out[k] = {"tg": "+", "wt": "?"}
            elif s == "-":   out[k] = {"tg": "-", "wt": "+"}
            elif s == "het": out[k] = {"tg": "+", "wt": "+"}
            else:            out[k] = {"tg": "?", "wt": "?"}
    return out

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"animals": [], "cages": [], "cohorts": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    # migrate missing keys
    if "cohorts" not in d:
        d["cohorts"] = []
    # migrate genes to new {tg, wt} format
    changed = False
    for a in d.get("animals", []):
        if a.get("genes"):
            new_g = migrate_gene_format(a["genes"])
            if new_g != a["genes"]:
                a["genes"] = new_g
                changed = True
    if changed:
        save_data(d)
    return d

def save_data(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def make_backup():
    if not os.path.exists(DATA_FILE):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = os.path.join(BACKUP_DIR, f"backup_{stamp}.json")
    shutil.copy2(DATA_FILE, dest)
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")], reverse=True)
    for old in backups[30:]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return dest

# ── handler ───────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.command:<8} {self.path.split('?')[0]:<40} {args[1]}")

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control",  "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, ctype):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type",   ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path == "/":
            self.send_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/api/data":
            self.send_json(load_data())
        elif path == "/api/backup":
            dest = make_backup()
            self.send_json({"ok": bool(dest), "file": os.path.basename(dest) if dest else ""})
        else:
            self.send_json({"error": "not found"}, 404)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        body = self.read_body()
        data = load_data()

        # animals
        if path == "/api/animals":
            body["id"] = str(uuid.uuid4())
            body["created_at"] = datetime.now().isoformat()
            data["animals"].append(body)
            save_data(data); self.send_json(body, 201)

        elif path.startswith("/api/animals/") and path.endswith("/update"):
            aid = path.split("/")[3]
            idx = next((i for i,a in enumerate(data["animals"]) if a["id"]==aid), None)
            if idx is None: self.send_json({"error":"not found"},404); return
            body["id"] = aid
            body["created_at"] = data["animals"][idx].get("created_at","")
            body["updated_at"] = datetime.now().isoformat()
            data["animals"][idx] = body
            save_data(data); self.send_json(body)

        # cages
        elif path == "/api/cages":
            body["id"] = str(uuid.uuid4())
            body["created_at"] = datetime.now().isoformat()
            data["cages"].append(body)
            save_data(data); self.send_json(body, 201)

        elif path.startswith("/api/cages/") and path.endswith("/update"):
            cid = path.split("/")[3]
            idx = next((i for i,c in enumerate(data["cages"]) if c["id"]==cid), None)
            if idx is None: self.send_json({"error":"not found"},404); return
            body["id"] = cid
            body["created_at"] = data["cages"][idx].get("created_at","")
            body["updated_at"] = datetime.now().isoformat()
            data["cages"][idx] = body
            save_data(data); self.send_json(body)

        # cohorts
        elif path == "/api/cohorts":
            body["id"] = str(uuid.uuid4())
            body["created_at"] = datetime.now().isoformat()
            data["cohorts"].append(body)
            save_data(data); self.send_json(body, 201)

        elif path.startswith("/api/cohorts/") and path.endswith("/update"):
            hid = path.split("/")[3]
            idx = next((i for i,c in enumerate(data["cohorts"]) if c["id"]==hid), None)
            if idx is None: self.send_json({"error":"not found"},404); return
            body["id"] = hid
            body["created_at"] = data["cohorts"][idx].get("created_at","")
            data["cohorts"][idx] = body
            save_data(data); self.send_json(body)

        # import
        elif path == "/api/import":
            mode     = body.get("mode","merge")
            incoming = body.get("animals",[])
            if mode == "replace":
                for a in incoming:
                    a["id"] = str(uuid.uuid4())
                    a["created_at"] = datetime.now().isoformat()
                data["animals"] = incoming
                added, skipped = len(incoming), 0
            else:
                existing = {a["mouse_id"] for a in data["animals"]}
                added = skipped = 0
                for a in incoming:
                    if a.get("mouse_id") in existing: skipped += 1
                    else:
                        a["id"] = str(uuid.uuid4())
                        a["created_at"] = datetime.now().isoformat()
                        data["animals"].append(a); added += 1
            save_data(data)
            self.send_json({"ok":True,"added":added,"skipped":skipped})

        else:
            self.send_json({"error":"not found"},404)

    # ── DELETE ────────────────────────────────────────────────────────────────
    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")
        data = load_data()

        if path.startswith("/api/animals/"):
            aid = path.split("/")[3]
            data["animals"] = [a for a in data["animals"] if a["id"]!=aid]
            save_data(data); self.send_json({"ok":True})

        elif path.startswith("/api/cages/"):
            cid = path.split("/")[3]
            data["cages"] = [c for c in data["cages"] if c["id"]!=cid]
            save_data(data); self.send_json({"ok":True})

        elif path.startswith("/api/cohorts/"):
            hid = path.split("/")[3]
            data["cohorts"] = [c for c in data["cohorts"] if c["id"]!=hid]
            save_data(data); self.send_json({"ok":True})

        else:
            self.send_json({"error":"not found"},404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║      MouseLog v3 — Colony Manager    ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"\n  ✓  Data   : {DATA_FILE}")
    print(f"  ✓  Backup : {BACKUP_DIR}/")
    print(f"  ✓  Server : http://localhost:{PORT}")
    print("\n  Open browser at  http://localhost:8888")
    print("  Ctrl+C to stop.\n")
    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped. Data is safe in mouselog_data.json")
