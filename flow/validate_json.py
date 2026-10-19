#!/usr/bin/env python3
"""Form check of the exchange files (orchestrator script; no technical judgement).
usage: validate_json.py EXCHANGE_DIR [FILE ...]   (default: every arch-/hdl-/tool- json in the directory)
Checks: valid JSON; envelope (from,to,round,block) equals the file name; no TODO; message ids unique per file; replies_to exist in the other side's files of the same block;
allowed words for kind/edge/storage/level fields; hdl-blk files carry rtl_map, ports, confidence, difficulty, control."""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage
ex = sys.argv[1]; files = sys.argv[2:] or sorted(glob.glob(os.path.join(ex, '*.json')))
KIND = {'pulse', 'level', 'held', 'data', 'n/a', 'unknown', 'none'}; EDGE = {'rising', 'falling', 'n/a', 'unknown'}; STOR = {'combinational', 'register', 'n/a', 'unknown'}
problems = []
def bad(f, msg): problems.append(f"{os.path.basename(f)}: {msg}")
def walk(o, fn, path=''):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, fn, f'{path}.{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, fn, f'{path}[{i}]')
    else: fn(path, o)
for f in files:
    name = os.path.basename(f)
    m = re.match(r'^(arch|hdl|tool)-(top|blk\d+)-(model|harness|rtl|regression|check)-v(\d+)\.json$', name) or re.match(r'^(tool)-(blk\d+|top)-(check|regression)-v(\d+)\.json$', name)
    if not m: bad(f, 'file name does not follow <from>-<top|blkN>-<kind>-v<K>.json'); continue
    try: d = json.load(open(f))
    except Exception as e: bad(f, f'invalid JSON: {e}'); continue
    frm, blk, kind, k = m.group(1), m.group(2), m.group(3), int(m.group(4))
    for key in ('from', 'to', 'round', 'block'):
        if key not in d: bad(f, f'envelope field {key!r} missing')
    if d.get('from') != frm: bad(f, f"envelope from={d.get('from')!r} but file name says {frm!r}")
    if d.get('block') != blk: bad(f, f"envelope block={d.get('block')!r} but file name says {blk!r}")
    if d.get('round') != k: bad(f, f"envelope round={d.get('round')!r} but file name says v{k}")
    if 'skills_used' in d and not (isinstance(d['skills_used'], list) and all(isinstance(x, str) for x in d['skills_used'])): bad(f, 'skills_used must be a list of strings')
    walk(d, lambda p, v: bad(f, f'TODO left at {p}') if isinstance(v, str) and 'TODO' in v else None)
    ids = []
    for sec in ('to_hdl', 'questions', 'assumptions', 'rtl_changes', 'decisions', 'replies'):
        for it in d.get(sec, []) if isinstance(d.get(sec), list) else []:
            if 'id' in it: ids.append(it['id'])
    if len(ids) != len(set(ids)): bad(f, 'message ids are not unique')
    if frm == 'hdl' and kind == 'rtl' and blk != 'top':
        for key in ('rtl_map', 'ports', 'confidence', 'difficulty', 'control', 'status'):
            if key not in d: bad(f, f'field {key!r} missing')
        for side in ('inputs', 'outputs'):
            for p in d.get('ports', {}).get(side, []):
                r = p.get('rtl', {})
                if r.get('kind') not in KIND: bad(f, f"{side} {p.get('arch_port')}: kind {r.get('kind')!r} not allowed")
                if r.get('edge') not in EDGE: bad(f, f"{side} {p.get('arch_port')}: edge {r.get('edge')!r} not allowed")
                if r.get('storage') not in STOR: bad(f, f"{side} {p.get('arch_port')}: storage {r.get('storage')!r} not allowed")
                if r.get('signal') not in ('none',) and not r.get('source'): bad(f, f"{side} {p.get('arch_port')}: no source (evidence)")
        # a signal field must be usable by the tools: RTL signal names joined with '+', a constant =VALUE, or none/unknown/n/a; not prose
        SIGTOK = r"[A-Za-z_][\w$]*(\[[^\]\s]*\])*(\.[A-Za-z_][\w$]*(\[[^\]\s]*\])*)*"   # hierarchical name; every part may carry [index] or [hi:lo]
        SIGOK = re.compile(rf"^(=[0-9a-fA-F_xXzZ']+|{SIGTOK}(\+{SIGTOK})*)$")
        sigs = [(f"{side} {p.get('arch_port')}", (p.get('rtl') or {}).get('signal')) for side in ('inputs', 'outputs') for p in d.get('ports', {}).get(side, [])] + [(f"extra_ports {e.get('signal')}", e.get('signal')) for e in d.get('extra_ports', [])]
        for where, sg in sigs:
            if isinstance(sg, str) and re.match(r'^=\s*(none|unknown|n/a)$', sg.strip(), re.I):
                bad(f, f"{where}: signal {sg!r}: 'none' (no RTL signal for this port) is written without '='; '=VALUE' is only for a constant (for example =3)"); continue
            if isinstance(sg, str) and sg not in ('none', 'unknown', 'n/a') and not SIGOK.match(sg.strip()):
                bad(f, f"{where}: signal {sg[:60]!r} is not a signal name the tools can probe (use the RTL name, several joined with '+', a constant as =VALUE; explanations go in 'source' or 'unknown')")
        # confidence and status must agree with the tool's evidence: a function check with 0 rows is no evidence
        hr = d.get('harness_result') or {}; fcr = (hr.get('function_check') or {}).get('rows')
        if fcr == 0:
            rmc = hr.get('register_mapping_check') or {}
            alt = d.get('alternative_evidence') or (rmc.get('expected_values') and rmc.get('seen_in_order') == rmc.get('expected_values'))
            if isinstance(d.get('confidence'), dict) and d['confidence'].get('level') == 'high': bad(f, "confidence 'high' although the function check compared 0 rows (use low or medium, or give 'alternative_evidence')")
            if d.get('status') == 'aligned' and not alt: bad(f, "status 'aligned' although the function check compared 0 rows and no 'alternative_evidence' is given (use open, or give the evidence)")
        for key, allowed in (('confidence', {'high', 'medium', 'low'}), ('difficulty', {'easy', 'medium', 'hard'})):
            if isinstance(d.get(key), dict) and d[key].get('level') not in allowed: bad(f, f'{key}.level must be one of {sorted(allowed)}')
        if isinstance(d.get('control'), dict) and d['control'].get('assessment') not in ('consistent', 'suspect', 'unknown'): bad(f, 'control.assessment must be consistent|suspect|unknown')
        if d.get('status') not in ('aligned', 'open', 'stuck'): bad(f, 'status must be aligned|open|stuck')
usage.log(ex, 'validate_json', files=len(files), problems=len(problems))
print(f'{len(files)} file(s) checked, {len(problems)} problem(s)')
for p in problems: print('  -', p)
sys.exit(1 if problems else 0)
