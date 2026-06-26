"""Regenerate every tracker + the dashboard, in dependency order. Run: python src/run_all.py"""
import os, subprocess, sys
SRC = os.path.dirname(os.path.abspath(__file__))
for script in ["adoption_monitor.py", "takeoff_tracker.py", "canaries.py", "canaries_employment.py",
               "canaries_lfs.py", "canaries_lfs_detail.py", "canaries_lfs_hiring.py", "build_dashboard.py"]:
    print(f"\n=== {script} ===")
    r = subprocess.run([sys.executable, os.path.join(SRC, script)])
    if r.returncode != 0:
        print(f"!! {script} failed (exit {r.returncode})"); sys.exit(r.returncode)
print("\nAll trackers + dashboard rebuilt -> dashboard/index.html")
