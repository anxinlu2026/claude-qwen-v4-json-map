#!/usr/bin/env python3
"""Set one field of a JSON exchange file without copying text around, then run the form check on that file and print its result.
usage: set_field.py FILE PATH=VALUE [PATH=VALUE ...]
PATH is dotted with [index] for lists, e.g.  status=open   confidence.level=low   ports.inputs[0].rtl.signal=tb.x.y   assumptions[1].status=refuted
VALUE is read as JSON when it parses (numbers, true/false/null, [..], {..}, "text"); otherwise it is taken as plain text.
Only the named fields change; the rest of the file is kept (the file is rewritten with 1-space indentation)."""
import io, json, os, re, subprocess, sys
f = sys.argv[1]; d = json.load(open(f))
def walk(path):
    toks = re.findall(r'[^.\[\]]+|\[\d+\]', path); return [int(t[1:-1]) if t.startswith('[') else t for t in toks]
for item in sys.argv[2:]:
    path, _, val = item.partition('=')
    try: v = json.loads(val)
    except Exception: v = val
    toks = walk(path); cur = d
    for t in toks[:-1]:
        try: cur = cur[t]
        except (KeyError, IndexError, TypeError): sys.exit(f"path not found: {path} (stopped at {t!r}); existing keys here: {list(cur)[:12] if isinstance(cur, dict) else len(cur)}")
    last = toks[-1]
    if isinstance(cur, dict) and last not in cur: sys.exit(f"no field {last!r} in {path}; existing keys: {list(cur)[:15]} (a new field is added only through the file's own sections)")
    old = cur[last]; cur[last] = v; print(f"{path}: {json.dumps(old, ensure_ascii=False)[:70]} -> {json.dumps(v, ensure_ascii=False)[:70]}")
json.dump(d, open(f, 'w'), ensure_ascii=False, indent=1)
here = os.path.dirname(os.path.abspath(__file__)); ex = os.path.dirname(os.path.abspath(f))
r = subprocess.run([sys.executable, os.path.join(here, 'validate_json.py'), ex, os.path.abspath(f)], capture_output=True, text=True); print(r.stdout.strip())
