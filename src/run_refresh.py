"""Unified monthly refresh — re-checks every tracker, rebuilds the 4 dashboard pages, and writes
an audit table of what each step did. Resilient: a failed tracker logs and continues (the last
committed CSVs are kept), so a single down source never blocks the rest.

Local microdata note: the LFS person files are EUL-protected and live only on the local machine.
In a headless runner (e.g. GitHub Actions) the canaries_lfs_* steps self-skip and the committed
aggregate CSVs are reused for the labour-market page.

Run: python src/run_refresh.py
"""
import csv, datetime, hashlib, os, subprocess, sys

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
AUDIT = os.path.join(ROOT, "data", "refresh_status.csv")

STEPS = [
    ("adoption_monitor.py",    "Adoption — BICS firms (live) + OPN sentiment (live)"),
    ("takeoff_tracker.py",     "Transformation — 9 live macro series"),
    ("canaries.py",            "Labour — Textkernel job adverts (live)"),
    ("canaries_employment.py", "Labour — APS employment, Nomis (live)"),
    ("canaries_lfs.py",        "Labour — LFS age x exposure (local-only)"),
    ("canaries_lfs_detail.py", "Labour — LFS gradient/roles/WFH (local-only)"),
    ("canaries_lfs_hiring.py", "Labour — LFS hiring gate (local-only)"),
    ("build_dashboard.py",     "Dashboard — rebuild the 4 HTML pages"),
]


def _signature():
    """Hash of the data/ + dashboard/ outputs, to tell whether the refresh produced anything new.
    Excludes the audit file itself (it always changes) so a no-op run stays a no-op."""
    h = hashlib.sha256()
    for base in ("data", "dashboard"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                if os.path.abspath(p) == os.path.abspath(AUDIT):
                    continue
                h.update(p.encode())
                try:
                    h.update(open(p, "rb").read())
                except OSError:
                    pass
    return h.hexdigest()


def _prepend_status(date, ok, failed):
    """Add a dated entry to the top of STATUS.md (running log, newest first)."""
    path = os.path.join(ROOT, "STATUS.md")
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError:
        return
    heading = f"## {date} — Automated monthly refresh"
    if len(lines) > 1 and lines[1].strip() == heading:
        return                                              # already logged today
    entry = [
        f"## {date} — Automated monthly refresh",
        f"Ran `run_refresh.py` across all tracks and rebuilt the 4 dashboard pages "
        f"({ok}/{ok + len(failed)} steps ok). Audit table in `data/refresh_status.csv`.",
    ]
    if failed:
        entry.append(f"**Failed/incomplete steps:** {', '.join(failed)} (kept last committed data).")
    lines[1:1] = entry + [""]
    open(path, "w", encoding="utf-8").write("\n".join(lines))


def main():
    date = datetime.date.today().isoformat()
    before = _signature()
    rows, failed = [], []
    for script, label in STEPS:
        proc = subprocess.run([sys.executable, os.path.join(SRC, script)],
                              capture_output=True, text=True)
        ok = proc.returncode == 0
        blob = (proc.stdout or "") + (proc.stderr or "")
        tail = blob.strip().splitlines()[-1] if blob.strip() else ""
        rows.append({"date": date, "step": script, "track": label,
                     "status": "ok" if ok else "FAILED", "detail": tail[:200]})
        print(f"[{'OK ' if ok else 'ERR'}] {script:26s} {tail[:110]}")
        if not ok:
            failed.append(script)

    with open(AUDIT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "step", "track", "status", "detail"])
        w.writeheader()
        w.writerows(rows)

    if "build_dashboard.py" in failed:
        print("\n!! build_dashboard.py failed — nothing to publish.")
        return 1

    changed = _signature() != before
    if changed:
        _prepend_status(date, len(rows) - len(failed), failed)
    print(f"\nRefresh complete: {len(rows) - len(failed)}/{len(rows)} steps ok. "
          f"Outputs {'changed' if changed else 'unchanged (no new data)'}. Audit -> data/refresh_status.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
