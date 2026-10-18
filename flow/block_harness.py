#!/usr/bin/env python3
"""Block-level harness runner (host side; calls `rtl` through the wrapper on PATH, which executes in the container).
Reads hdl-blk<N>-rtl-v<K>.json (the RTL signals the HDL engineer mapped) and arch-blk<N>-model/harness-v<K>.json, then:
  function check: RTL's own probed block inputs -> python model block -> compare with the RTL block outputs (rtl blockcheck)
  input check:    the inputs the RTL actually gives the block, compared with the harness inputs (testbench stimulus through the model chain), in step order
It writes both results into the HDL json ("harness_result") and into tool-blk<N>-check-v<K>.json, so the numbers are from the tool, not typed by hand.
usage: block_harness.py EXCHANGE_DIR BLK_NUMBER [ROUND] [--when "rtl condition"] [--model-dir /tmp/ip_work/arch] [--no-write]
The HDL json may carry "active_when": "<rtl expression>" at top level (the condition under which the block works; rtl blockcheck --when)."""
import json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage
a = [x for x in sys.argv[1:] if not x.startswith('--')]; opts = {}
argv = sys.argv[1:]; i = 0
while i < len(argv):
    if argv[i] in ('--when', '--model-dir'): opts[argv[i]] = argv[i + 1]; i += 2
    else:
        if argv[i] == '--no-write': opts['--no-write'] = True
        i += 1
ex, n = a[0], int(a[1]); K = int(a[2]) if len(a) > 2 else 0
mdir = opts.get('--model-dir', '/tmp/ip_work/arch')
hp = os.path.join(ex, f'hdl-blk{n}-rtl-v{K}.json'); H = json.load(open(hp))
M = json.load(open(os.path.join(ex, f'arch-blk{n}-model-v{K}.json'))); HA = json.load(open(os.path.join(ex, f'arch-blk{n}-harness-v{K}.json')))
fn = M['python']['function']; bid = M['name']
ports = H['ports']; ins = ports['inputs']; outs = ports['outputs']
order = [p['name'] for p in M['ports']['inputs']]
byname = {p['arch_port']: p for p in ins}
sigs = []
for nm in order:
    p = byname.get(nm)
    if not p or p['rtl']['signal'] in ('none', 'TODO', 'unknown', 'n/a'): sigs.append(None); continue
    sigs.append(p['rtl']['signal'])
res = {"block": f"blk{n}", "name": bid, "round": K, "time": time.strftime('%Y-%m-%d %H:%M:%S'), "inputs_in_model_order": order, "rtl_input_signals": sigs}
if None in sigs or not outs or outs[0]['rtl']['signal'] in ('none', 'TODO', 'unknown', 'n/a'):
    res["error"] = "RTL signals missing for some model input/output port; fill them (or write 'none') before running the harness"
    print(res['error']); print('missing inputs:', [order[j] for j, s in enumerate(sigs) if s is None]); sys.exit(2)
outsig = outs[0]['rtl']['signal']
when = opts.get('--when') or H.get('active_when')
cmd = ['rtl', 'blockcheck', '--in'] + sigs + ['--out', outsig, '--model', f'python3 {mdir}/model_cli.py block {bid}', '--max', '40']
if when: cmd += ['--when', when]
t = subprocess.run(cmd, capture_output=True, text=True); text = t.stdout + t.stderr
rows = []
for line in text.splitlines():
    c = [x.strip() for x in line.split('|')]
    if len(c) >= len(sigs) + 4 and c[0].isdigit():
        rows.append({"t": int(c[0]), "inputs": c[1:1 + len(sigs)], "rtl_out": c[1 + len(sigs)], "model_out": c[2 + len(sigs)], "result": c[-1]})
ok = sum(1 for r in rows if r['result'] == 'match'); bad = sum(1 for r in rows if r['result'].startswith('MISMATCH'))
res["function_check"] = {"command": ' '.join(cmd), "rows": len(rows), "match": ok, "mismatch": bad, "raw": text[-3500:]}
# fallback for blocks without a model_cli entry (state / selection blocks): compare by VALUE with the harness steps
if len(rows) == 0:
    pc = ['rtl', 'probe'] + sigs + [outsig, '--max', '40'] + (['--when', when] if when else [])
    pt = subprocess.run(pc, capture_output=True, text=True); ptext = pt.stdout + pt.stderr; prow = []
    for line in ptext.splitlines():
        c = [x.strip() for x in line.split('|')]
        if len(c) >= len(sigs) + 2 and c[0].isdigit(): prow.append({"t": int(c[0]), "inputs": c[1:1 + len(sigs)], "rtl_out": c[1 + len(sigs)]})
    def numv(x):
        try: return int(str(x).lower().replace('0x', ''), 16)
        except ValueError: return None
    vm = vb = vn = 0; vrows = []
    for r in prow:
        hit = None
        for s_ in HA['steps']:
            want = [s_['inputs'].get(nm) for nm in order]
            if all(w in (None, 'n/a') or (numv(w) is not None and numv(w) == numv(g)) for w, g in zip(want, r['inputs'])): hit = s_; break
        outn = list(hit['outputs'].values())[0] if hit else None
        if hit is None: vn += 1; r['result'] = 'no harness step has these inputs'
        elif numv(outn) == numv(r['rtl_out']): vm += 1; r['result'] = 'match'
        else: vb += 1; r['result'] = 'MISMATCH'; r['harness_out'] = outn
        vrows.append(r)
    rows = [{"t": r['t'], "inputs": r['inputs'], "rtl_out": r['rtl_out'], "model_out": r.get('harness_out', r['rtl_out'] if r['result'] == 'match' else ''), "result": r['result']} for r in vrows]
    ok, bad = vm, vb
    res["function_check"] = {"command": " ".join(pc), "rows": len(rows), "match": ok, "mismatch": bad, "raw": ptext[-3500:]}
    res["function_check_mode"] = "harness-values (no model_cli entry for this block): RTL row inputs matched to a harness step by value; rows with no such step: %d" % vn
    text = ptext
# per-byte difference summary for the first mismatching rows (helps the architect see the pattern; no interpretation)
diffs = []
for r in rows:
    if r['result'].startswith('MISMATCH') and len(r['rtl_out']) == len(r['model_out']) and len(diffs) < 6:
        try: diffs.append({"t": r['t'], "xor_per_byte": [format(int(r['rtl_out'][k:k + 2], 16) ^ int(r['model_out'][k:k + 2], 16), '02x') for k in range(0, len(r['rtl_out']), 2)]})
        except ValueError: pass
res["function_check"]["xor_of_rtl_and_model_by_byte"] = diffs
# input check: harness inputs vs the inputs the RTL gave, step by step (hex compare, numbers compared as integers)
def num(x):
    try: return int(str(x).lower().replace('0x', ''), 16)
    except ValueError: return None
steps = HA['steps']; hit = 0; first_bad = None; pos = 0
for s_ in steps:
    want = [s_['inputs'].get(nm) for nm in order]
    found = False
    for j in range(pos, len(rows)):
        got = rows[j]['inputs']
        if all(w in (None, 'n/a') or (num(w) is not None and num(w) == num(g)) for w, g in zip(want, got)): found = True; pos = j + 1; break
    if found: hit += 1
    elif first_bad is None: first_bad = {"step": s_['step'], "wanted": dict(zip(order, want))}
res["mismatch_rows_compact"] = [{"t": r["t"], "rtl_out": r["rtl_out"], "model_out": r["model_out"]} for r in rows if r["result"].startswith("MISMATCH")][:8]
res["input_check"] = {"steps": len(steps), "steps_whose_inputs_were_seen_in_order": hit, "not_seen": len(steps) - hit, "first_step_not_seen": first_bad}
json.dump(res, open(os.path.join(ex, f'tool-blk{n}-check-v{K}.json'), 'w'), ensure_ascii=False, indent=1)
if not opts.get('--no-write'):
    H['harness_result'] = {"function_check": {"rows": len(rows), "match": ok, "mismatch": bad, "raw": f"tool-blk{n}-check-v{K}.json"},
                           "input_check": {"rows": len(steps), "match": hit, "mismatch": len(steps) - hit, "raw": f"tool-blk{n}-check-v{K}.json"}}
    json.dump(H, open(hp, 'w'), ensure_ascii=False, indent=1)
usage.log(ex, 'block_harness', block=f'blk{n}', round=K, function_rows=len(rows), function_match=ok, function_mismatch=bad, input_steps=len(steps), input_seen=hit, mode=res.get('function_check_mode', 'model_cli'))
print(f"blk{n} {bid}: function check rows {len(rows)}  match {ok}  mismatch {bad}   |   input check: {hit}/{len(steps)} harness steps' inputs seen in order")
if first_bad: print('  first harness step whose inputs the RTL never gave:', json.dumps(first_bad)[:300])
for d in diffs[:3]: print('  mismatch row t=%s: xor(rtl,model) per byte: %s' % (d['t'], ' '.join(d['xor_per_byte'])))
