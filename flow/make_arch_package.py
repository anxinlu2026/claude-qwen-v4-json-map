#!/usr/bin/env python3
"""Architecture package v<K> for the block-map flow, generated from the architecture's own model (pilot/arch/model.json + model.py):
  arch-top-model-v<K>.json, arch-blk<N>-model-v<K>.json, arch-blk<N>-harness-v<K>.json
Harness steps: the top testbench stimulus (key, ciphertext) pushed through the python model chain; expected values come from the model
(the chain's end result is checked against the testbench's expected plaintext). Nothing here reads RTL.
usage: make_arch_package.py OUTDIR [ROUND]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ARCH = os.path.normpath(os.path.join(HERE, '..', 'pilot', 'arch'))
sys.path.insert(0, ARCH)
import model as m
out = sys.argv[1]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 0
os.makedirs(out, exist_ok=True)
D = json.load(open(os.path.join(ARCH, 'model.json')))
KEY = 0x2b7e151628aed2a6abf7158809cf4f3c; CT = 0x3925841d02dc09fbdc118597196a0b32; PT = 0x3243f6a8885a308d313198a2e0370734
hx = lambda b: bytes(b).hex()
ENV = lambda to, block: {"from": "arch", "to": to, "round": K, "block": block}

# ---- trace of the model chain on the testbench vector (per block, per step)
rks = m.key_expansion(m.to_bytes(KEY)); st = {}
def rec(blk, step, cond, ins, outs): st.setdefault(blk, []).append({"step": step, "model_condition": cond, "inputs": ins, "outputs": outs})
s = m.load_block(CT); rec('load_block', 0, 'start row, i_data = testbench ciphertext', {"i_data": hx(s)}, {"state_in": hx(s)})
rk_all = ''.join(hx(r) for r in rks[::-1])      # rk[0] = most significant in the model_cli convention is documented there; kept as in model_cli
for n in range(1, 11):
    prev = rks[n - 1]; w3 = prev[12:16]; rot = m.rot_word(w3); sub = m.sub_word(rot); t = m.rcon_xor(sub, n); nxt = m.next_round_key(prev, n)
    c = f'key expansion step n={n}'
    rec('key_expand_step', n, c, {"prev_round_key": hx(prev), "n": n}, {"next_round_key": hx(nxt)})
    rec('rot_word', n, c, {"w3": hx(w3)}, {"rot": hx(rot)}); rec('sub_word', n, c, {"rot": hx(rot)}, {"sub": hx(sub)})
    rec('rcon_step', n, c, {"sub": hx(sub), "n": n}, {"t": hx(t)}); rec('word_xor_chain', n, c, {"prev_round_key": hx(prev), "t": hx(t)}, {"next_round_key": hx(nxt)})
    rec('round_key_store', n, c, {"next_round_key": hx(nxt)}, {"round_key[%d]" % n: hx(nxt)})
for r in range(1, 12):
    k = rks[m.round_key_index(r)]; c = f'round_cnt = {r}'
    rec('round_key_select', r, c, {"round_cnt": r, "rk_all": rk_all}, {"round_key": hx(k)})
    if r == 1:
        a = m.add_round_key(s, k); rec('add_round_key', r, c, {"state": hx(s), "round_key": hx(k)}, {"state_out": hx(a)})
        rec('round_mux', r, c, {"initial_path": hx(a), "round_path": "n/a", "final_path": "n/a", "round_cnt": r}, {"state_next": hx(a)}); ns = a
    else:
        sr = m.inv_shift_rows(s); rec('inv_shift_rows', r, c, {"state": hx(s)}, {"state_out": hx(sr)})
        sb = m.inv_sub_bytes(sr); rec('inv_sub_bytes', r, c, {"state": hx(sr)}, {"state_out": hx(sb)})
        a = m.add_round_key(sb, k); rec('add_round_key', r, c, {"state": hx(sb), "round_key": hx(k)}, {"state_out": hx(a)})
        if r <= 10:
            mc = m.inv_mix_columns(a); rec('inv_mix_columns', r, c, {"state": hx(a)}, {"state_out": hx(mc)})
            rec('round_mux', r, c, {"initial_path": "n/a", "round_path": hx(mc), "final_path": "n/a", "round_cnt": r}, {"state_next": hx(mc)}); ns = mc
        else:
            rec('round_mux', r, c, {"initial_path": "n/a", "round_path": "n/a", "final_path": hx(a), "round_cnt": r}, {"state_next": hx(a)}); ns = a
    rec('state_reg', r, c, {"state_next": hx(ns)}, {"state": hx(ns)}); s = ns
rec('output_map', 12, 'o_done = 1', {"q": hx(s)}, {"o_data": hx(s)})
assert m.to_int(s) == PT == m.decrypt_block(CT, KEY), 'model chain does not reproduce the testbench plaintext'

# ---- files
order = [b['id'] for b in D['blocks'] if b['kind'] in ('datapath', 'register')]
bn = {bid: i for i, bid in enumerate(order)}
files = []
top = {**ENV('hdl', 'top'), "design": {"name": D['design'] if isinstance(D['design'], str) else D['design'].get('name', 'aes128_decrypt'), "spec_ref": "task prompt (prompt.json) + FIPS 197 (resources/standards/aes)"},
       "design_ports": [{"name": p['name'], "dir": p['dir'], "width": p['width'], "kind": p.get('role', ''), "clock": 'clk' if p['name'] != 'clk' else 'none', "edge": p.get('edge', 'rising' if p.get('role') != 'clock' else 'n/a'),
                         "function": p.get('function', ''), "timing": p.get('timing', '')} for p in D['interface']],
       "blocks": [{"id": f"blk{bn[b]}", "name": b, "order": bn[b], "file": f"arch-blk{bn[b]}-model-v{K}.json", "harness": f"arch-blk{bn[b]}-harness-v{K}.json"} for b in order],
       "connections": [{"from": (lambda a: f"blk{bn[a.split('.')[0]]}.{a.split('.')[1]}" if a.split('.')[0] in bn else a)(e['from']),
                        "to": (lambda a: f"blk{bn[a.split('.')[0]]}.{a.split('.')[1]}" if a.split('.')[0] in bn else a)(e['to']), "when": e.get('when', 'always')} for e in D['edges']
                       if e['from'].split('.')[0] in bn or e['to'].split('.')[0] in bn or e['from'].startswith('design port') or e['to'].startswith('design port')],
       "control_blocks_note": "control blocks (key_counter, round_counter, done_gen, key_done_flag) are in the model; their behaviour is given as the schedule below and is what 'control assessment' is compared with",
       "schedule": D['schedule'], "byte_layout": D['byte_layout'],
       "order_note": "blocks are listed from input to output; the HDL engineer aligns them in this order",
       "harness": {"model_chain_result": "model chain reproduces the testbench plaintext (checked when this file was generated)", "testbench_stimulus": {"key": hex(KEY), "i_data": hex(CT)}, "expected_output": hex(PT)},
       "status": "open"}
files.append((f"arch-top-model-v{K}.json", top))
for b in D['blocks']:
    if b['id'] not in bn: continue
    n = bn[b['id']]; pd = b['ports_detail']
    mod = {**ENV('hdl', f'blk{n}'), "name": b['id'], "order": n, "function_text": b.get('function_detail') or b.get('function', ''), "spec_ref": "task prompt + FIPS 197",
           "ports": {"inputs": [{**{k: p[k] for k in ('name', 'width', 'kind', 'valid_when', 'clock', 'edge', 'storage', 'latency_min_cycles', 'latency_max_cycles')}, "connected_to": ', '.join(f"{c['block']}.{c['port']}" for c in p['connected_to'])} for p in pd['inputs']],
                     "outputs": [{**{k: p[k] for k in ('name', 'width', 'kind', 'valid_when', 'clock', 'edge', 'storage', 'latency_min_cycles', 'latency_max_cycles')}, "connected_to": ', '.join(f"{c['block']}.{c['port']}" for c in p['connected_to'])} for p in pd['outputs']]},
           "elements": [], "python": {"module": "model.py", "function": b['python'].split(':')[-1]}, "to_hdl": [], "decisions": [], "status": "open", "no_change": False}
    files.append((f"arch-blk{n}-model-v{K}.json", mod))
    files.append((f"arch-blk{n}-harness-v{K}.json", {**ENV('hdl', f'blk{n}'), "source": "top testbench stimulus -> python model chain dump", "end_to_end_check": "chain output == testbench expected plaintext",
                  "steps": st.get(b['id'], []), "expected_activity": [{"active_when": b.get('timing', {}).get('valid_when', 'always'), "type": b.get('timing', {}).get('type', '')}], "register_expected": []}))
for name, obj in files:
    json.dump(obj, open(os.path.join(out, name), 'w'), ensure_ascii=False, indent=1)
print(f"wrote {len(files)} files to {out}; blocks in order: {order}")
