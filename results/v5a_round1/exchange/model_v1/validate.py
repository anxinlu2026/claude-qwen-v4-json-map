"""Runs harness_check.py; prints HARNESS PASS only if it ends with ALL PASS."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, os.path.join(here, "harness_check.py"), "100"], cwd=here, capture_output=True, text=True)
print(r.stdout, end="")
if r.stderr:
    print(r.stderr, end="")
ok = r.returncode == 0 and r.stdout.strip().endswith("ALL PASS")
print("HARNESS PASS" if ok else "HARNESS FAIL")
sys.exit(0 if ok else 1)
