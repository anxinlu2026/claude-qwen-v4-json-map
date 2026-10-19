#!/usr/bin/env python3
"""Live view of the HDL model's work in a cell driven by run_hdl_cc.py: reads the Claude Code session transcript and the exchange folder,
prints one line per minute with the new tool calls (name and a short form of the input), new hdl/tool files, and the turn log.
usage: watch_hdl.py CELL_DIR [--interval 60] [--quiet]   (--quiet: print only when a new hdl/tool file appears, a turn ends or the driver ends)"""
import glob, json, os, sys, time
cell = sys.argv[1]; iv = int(sys.argv[sys.argv.index('--interval') + 1]) if '--interval' in sys.argv else 60
quiet = '--quiet' in sys.argv; lastloop = None
ex = os.path.join(cell, 'exchange'); seen = {}; files = set(); logn = 0; first = True
def short(i):
    for k in ('command', 'file_path', 'path', 'pattern'):
        if k in i: return str(i[k]).replace('\n', ' ')[:110]
    return json.dumps(i, ensure_ascii=False)[:110]
while True:
    new = []
    for p in glob.glob(os.path.join(cell, 'cc_cfg', 'projects', '*', '*.jsonl')):
        n0 = seen.get(p, 0); lines = open(p, errors='replace').read().splitlines(); seen[p] = len(lines)
        for l in lines[n0:]:
            try: e = json.loads(l)
            except Exception: continue
            m = e.get('message') or {}
            if isinstance(m.get('content'), list):
                for c in m['content']:
                    if c.get('type') == 'tool_use': new.append((c['name'], short(c.get('input', {}))))
    # loop detector: the same tool call repeated three times in a row in the newest transcript
    loop = None
    ps = sorted(glob.glob(os.path.join(cell, 'cc_cfg', 'projects', '*', '*.jsonl')), key=os.path.getmtime)
    if ps:
        calls = []
        for l in open(ps[-1], errors='replace'):
            try: e = json.loads(l)
            except Exception: continue
            m = e.get('message') or {}
            if isinstance(m.get('content'), list):
                calls += [json.dumps(c.get('input', {}), sort_keys=True) for c in m['content'] if c.get('type') == 'tool_use']
        if len(calls) >= 3 and calls[-1] == calls[-2] == calls[-3] and calls[-1] != lastloop: loop = calls[-1][:150]; lastloop = calls[-1]
    if loop: print(time.strftime('%H:%M:%S'), 'LOOP DETECTED: the same call 3 times in a row:', loop, flush=True)
    cur = {f for f in os.listdir(ex) if f.startswith(('hdl-', 'tool-')) and f.endswith('.json')}; nf = sorted(cur - files); files = cur
    lp = os.path.join(ex, 'hdl-session-log.jsonl'); turns = []
    if os.path.exists(lp):
        L = open(lp).read().splitlines(); turns = [json.loads(x) for x in L[logn:]]; logn = len(L)
    if (nf or turns) if quiet else (new or nf or turns or first):
        t = time.strftime('%H:%M:%S'); v0 = sum(1 for f in cur if f.startswith('hdl-') and f.endswith('-v0.json'))
        print(f'{t} tools+{len(new)}' + (f' last: {new[-1][0]} {new[-1][1]}' if new else '') + (f' | new files: {", ".join(nf)[:160]}' if nf else '') + f' | hdl-v0 files {v0}', flush=True)
        for r in turns: print(f'   turn {r["turn"]} ended: {r["seconds"]} s, model turns {r.get("model_turns")}, tokens in/out {r.get("input_tokens")}/{r.get("output_tokens")}, progress {r["progress"]}', flush=True)
    first = False
    if not any(True for _ in os.popen('pgrep -f run_hdl_cc.py')): print(time.strftime('%H:%M:%S'), 'driver ended', flush=True); break
    time.sleep(iv)
