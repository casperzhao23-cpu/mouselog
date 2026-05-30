#!/usr/bin/env python3
"""
MouseLog — Daily Reminder
Reads mouselog_data.json, computes each animal's task dates from DOB + age,
and sends Mac notifications for tasks due today (within reminder window).

One-time setup:
  1. Open a new Terminal window
  2. Run: crontab -e
  3. Press i, paste the line below (edit path), press Esc then type :wq and Enter
     30 8 * * * /usr/bin/python3 "/Users/casperzhao/Desktop/HE LAB/MouseLog/remind.py"

To test immediately:
  python3 "/Users/casperzhao/Desktop/HE LAB/MouseLog/remind.py"
"""

import json, os, subprocess, math
from datetime import date, datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mouselog_data.json")

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}")

def notify(title, body, subtitle=""):
    s = lambda t: t.replace('"', '\\"').replace("'", "\\'")
    sub = f'subtitle "{s(subtitle)}"' if subtitle else ''
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{s(body)}" with title "{s(title)}" {sub}'],
            check=True, capture_output=True
        )
    except Exception as e:
        log(f"  Notification error: {e}")

def age_to_date(dob_str, age_val, age_unit):
    """Compute the target date from DOB + age."""
    try:
        dob = date.fromisoformat(dob_str)
        age_val = float(age_val)
    except:
        return None
    if age_unit == "weeks":
        days = round(age_val * 7)
    elif age_unit == "months":
        days = round(age_val * 30.44)
    else:  # days
        days = round(age_val)
    return dob + timedelta(days=days)

def main():
    log("=== MouseLog Daily Reminder ===")
    if not os.path.exists(DATA_FILE):
        log(f"Data file not found: {DATA_FILE}")
        notify("MouseLog", f"Data file not found:\n{DATA_FILE}")
        return

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    animals = data.get("animals", [])
    today   = date.today()
    tasks   = []

    skip_statuses = {"deceased", "sacrificed"}

    for a in animals:
        if a.get("status") in skip_statuses: continue
        dob_str = a.get("dob", "")
        if not dob_str: continue

        # timeline tasks
        for t in a.get("timeline", []):
            if t.get("done"):           continue
            if not t.get("label"):      continue
            age_val  = t.get("age_val", 0)
            age_unit = t.get("age_unit", "weeks")
            if not age_val:             continue

            target = age_to_date(dob_str, age_val, age_unit)
            if not target:              continue

            diff   = (today - target).days
            window = int(t.get("window_days", 1))

            if -window <= diff <= window:
                tasks.append({
                    "mouse_id":    a.get("mouse_id", "?"),
                    "label":       t["label"],
                    "target_date": target.isoformat(),
                    "age_val":     age_val,
                    "age_unit":    age_unit,
                    "diff":        diff,
                    "type":        "timeline",
                })

        # transfer reminders
        transfer_date_str = a.get("transfer_date", "")
        if transfer_date_str:
            try:
                transfer_date = date.fromisoformat(transfer_date_str)
                diff = (today - transfer_date).days
                if -1 <= diff <= 1:
                    target_cage = a.get("transfer_target_cage", "?")
                    tasks.append({
                        "mouse_id":    a.get("mouse_id", "?"),
                        "label":       f"Transfer → {target_cage}",
                        "target_date": transfer_date_str,
                        "diff":        diff,
                        "type":        "transfer",
                    })
            except:
                pass

    if not tasks:
        log("No tasks due today.")
        notify("MouseLog ✓",
               "No animal tasks due today.",
               subtitle=today.strftime("%B %d, %Y"))
        return

    tasks.sort(key=lambda x: -x["diff"])  # overdue first
    log(f"Found {len(tasks)} task(s):")

    lines = []
    for t in tasks:
        diff  = t["diff"]
        age   = f"{t['age_val']}{t['age_unit'][0]}"  # e.g. "8wk"
        tag   = "OVERDUE" if diff > 0 else "TODAY" if diff == 0 else f"in {-diff}d"
        line  = f"[{tag}] {t['mouse_id']} ({age}) — {t['label']}"
        lines.append(line)
        log(f"  {line}")

    body = "\n".join(lines[:5])
    if len(lines) > 5:
        body += f"\n…+{len(lines)-5} more tasks"

    notify(
        f"MouseLog — {len(tasks)} task{'s' if len(tasks)>1 else ''} today",
        body,
        subtitle=today.strftime("%B %d, %Y")
    )
    log("Notification sent. Done.")

if __name__ == "__main__":
    main()
