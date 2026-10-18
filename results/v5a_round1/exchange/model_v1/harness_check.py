"""Checks model.py against the testbench vectors, the hidden-test behaviour, the library model and model.json.
usage: python3 harness_check.py [runs_per_reset]   (default 100; the official test uses 1000)"""
import json, os, random, sys
import model as m
for _p in ("/opt/resources/ip_models/aes128", "/Users/anxin/AI/benchmarks/multi-ai/resources/ip_models/aes128"):
    if os.path.isdir(_p):
        sys.path.insert(0, _p)
        break
import aes_ref_qwen as lib

fails = 0
def check(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += 0 if ok else 1

KEY = 0x2b7e151628aed2a6abf7158809cf4f3c
CT = 0x3925841d02dc09fbdc118597196a0b32
PT = 0x3243f6a8885a308d313198a2e0370734
rnd = random.Random(1)

# --- 1. tables and blocks vs library model
check("sbox table (built from GF algebra) == library", m.SBOX == lib.SB and m.INV_SBOX == lib.INV_SB and m.RCON == lib.RCON)
def lst(b): return [[b[4 * c + r] for c in range(4)] for r in range(4)]
def flat(s): return [s[r][c] for c in range(4) for r in range(4)]
ok = True
for _ in range(200):
    st = [rnd.randrange(256) for _ in range(16)]; rk = [rnd.randrange(256) for _ in range(16)]
    ok &= m.inv_shift_rows(st) == flat(lib.inv_shift_rows(lst(st)))
    ok &= m.inv_sub_bytes(st) == flat(lib.inv_sub_bytes(lst(st)))
    ok &= m.inv_mix_columns(st) == flat(lib.inv_mix_columns(lst(st)))
    ok &= m.add_round_key(st, rk) == flat(lib.inv_add_round_key(lst(st), lst(rk)))
check("InvShiftRows / InvSubBytes / InvMixColumns / AddRoundKey == library (200 random states)", ok)
ok = True
for _ in range(100):
    k = bytes(rnd.randrange(256) for _ in range(16)); w = lib.key_expansion(k)
    rks = m.key_expansion(list(k))
    ok &= all(rks[i][4 * j:4 * j + 4] == w[4 * i + j] for i in range(11) for j in range(4))
check("key expansion (44 words) == library (100 random keys)", ok)
check("FIPS 197 A.1 last round key d014f9a8c9ee2589e13f0cc8b6630ca6",
      bytes(m.key_expansion(m.to_bytes(KEY))[10]).hex() == "d014f9a8c9ee2589e13f0cc8b6630ca6")
check("rot_word / sub_word / rcon step on FIPS A.1 (w3=09cf4f3c -> 8b84eb01)",
      m.rcon_xor(m.sub_word(m.rot_word([0x09, 0xcf, 0x4f, 0x3c])), 1) == [0x8b, 0x84, 0xeb, 0x01])
ok = True
for _ in range(100):
    k = bytes(rnd.randrange(256) for _ in range(16)); c = bytes(rnd.randrange(256) for _ in range(16))
    ok &= m.to_bytes(m.decrypt_block(int.from_bytes(c, "big"), int.from_bytes(k, "big"))) == list(lib.decrypt_block(c, k)[0])
check("decrypt_block == library decrypt_block (100 random)", ok)
check("decrypt_block on TB vector == 3243f6a8885a308d313198a2e0370734", m.decrypt_block(CT, KEY) == PT)

# --- 2. testbench scenario (tb_aes128_dec.sv): reset, Simple_test(1), Simple_test(0), same key/data
t = m.Top(); t.reset()
def tb_test(update):
    """start for exactly one row, inputs cleared; wait for rising edge of o_done; read o_data in that row."""
    t.step(1, update, KEY, CT)
    prev = t.view()["o_done"]; rows = 1
    assert prev == 0, "o_done must be 0 in row 1"
    while True:
        t.step(0, 0, 0, 0); rows += 1
        v = t.view()
        if v["o_done"] and not prev:
            return rows, v["o_data"]
        prev = v["o_done"]
        if rows > 200: return rows, None
r1, d1 = tb_test(1); check(f"TB Simple_test(1): o_data == expected, o_done row {r1}", d1 == PT)
t.step(0, 0, 0, 0); t.step(0, 0, 0, 0)       # idle rows between tests (TB waits a negedge or more)
r2, d2 = tb_test(0); check(f"TB Simple_test(0) with stored key: o_data == expected, o_done row {r2}", d2 == PT)

# --- 3. hidden test (test_aes128_decrypt.py): 4 resets x runs, random update_key, first run of each reset update=1
runs = int(sys.argv[1]) if len(sys.argv) > 1 else 100
t = m.Top(); ok_reset = ok_data = ok_pulse = True; cur_key = None; done_rows = {0: set(), 1: set()}
for i in range(4):
    t.reset(); t.step(); t.step()                       # reset low one clock, then high, two edges
    ok_reset &= t.view()["o_data"] == 0                  # AA5: model.reset() presumed to give 0
    for j in range(runs):
        key, data = rnd.getrandbits(128), rnd.getrandbits(128)
        upd = 1 if j == 0 else rnd.randint(0, 1)
        if upd: cur_key = key
        exp = m.decrypt_block(data, cur_key)
        t.step(1, upd, key, data); n = 1                 # edge Eb samples the start
        while True:                                      # edge Ec...: cocotb reads the view before the edge
            seen = t.view(); t.step(0, 0, 0, 0)
            if seen["o_done"]: break
            n += 1
        ok_data &= seen["o_data"] == exp
        done_rows[upd].add(n)
        ok_pulse &= t.view()["o_done"] == 0              # pulse ends before the next start
check(f"hidden test: o_data == model after each reset ({4} resets)", ok_reset)
check(f"hidden test: {4 * runs} runs, random update_key, all outputs correct", ok_data)
check("hidden test: o_done is a pulse (0 in the row after the done row)", ok_pulse)
check("hidden test: latency constant (update %s rows, no update %s rows)" % (sorted(done_rows[1]), sorted(done_rows[0])),
      len(done_rows[1]) == 1 and len(done_rows[0]) == 1)

# --- 4. model.json schedule vs the cycle model, JSON structure
js = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json")))
for case in js["schedule"]["cases"]:
    upd = 1 if case["case"] == "update" else 0
    rows, out = m.run_case(upd, KEY, CT)
    same = all(case[k] == [r[k] for r in rows] for k in ["i_start", "i_update_key", "key_cnt", "round", "key_done", "o_done"])
    check(f"model.json schedule '{case['case']}' == cycle model ({len(rows)} rows), output correct", same and out == PT)
# --- 5. model_cli.py (rtl blockcheck interface) against model.py
import subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
def cli(name, *args):
    return subprocess.run([sys.executable, os.path.join(HERE, "model_cli.py"), "block", name, *args],
                          capture_output=True, text=True).stdout.strip()
def h(b): return bytes(b).hex()
ok = {}
for _ in range(5):
    st = [rnd.randrange(256) for _ in range(16)]; rk = [rnd.randrange(256) for _ in range(16)]
    w = [rnd.randrange(256) for _ in range(4)]; n = rnd.randint(1, 10); r = rnd.randint(1, 11)
    allk = m.key_expansion(rk)
    exp = {
        "load_block": (m.load_block(int.from_bytes(bytes(st), "big")), [h(st)]),
        "output_map": ("%032x" % m.output_map(st), [h(st)]),
        "add_round_key": (m.add_round_key(st, rk), [h(st), h(rk)]),
        "inv_shift_rows": (m.inv_shift_rows(st), [h(st)]),
        "inv_sub_bytes": (m.inv_sub_bytes(st), [h(st)]),
        "inv_mix_columns": (m.inv_mix_columns(st), [h(st)]),
        "round_key_select": (allk[m.round_key_index(r)], [h(sum(allk, [])), "%x" % r]),
        "round_mux": (st if r == 1 else rk if r <= 10 else w * 4, [h(st), h(rk), h(w * 4), "%x" % r]),
        "rot_word": (m.rot_word(w), [h(w)]),
        "sub_word": (m.sub_word(w), [h(w)]),
        "rcon_step": (m.rcon_xor(w, n), [h(w), "%x" % n]),
        "word_xor_chain": (m.next_round_key(rk, n), None),
        "key_expand_step": (m.next_round_key(rk, n), [h(rk), "%x" % n]),
    }
    t = m.rcon_xor(m.sub_word(m.rot_word(rk[12:16])), n)
    exp["word_xor_chain"] = (m.next_round_key(rk, n), [h(rk), h(t)])
    for name, (e, args) in exp.items():
        e = e if isinstance(e, str) else h(e)
        ok[name] = ok.get(name, True) and cli(name, *args) == e
for name, v in ok.items():
    check(f"model_cli.py block {name} == model.py (5 random inputs)", v)

ids = {b["id"] for b in js["blocks"]}
check("model.json: sub_blocks and python refs exist", all(s in ids for b in js["blocks"] for s in b.get("sub_blocks", []))
      and all(hasattr(m, b["python"].split(":")[1].split(".")[0]) for b in js["blocks"]))
check("model.json: all 8 ports present", {p["name"] for p in js["interface"]} == {"clk", "rst_async_n", "i_update_key", "i_key", "i_start", "i_data", "o_done", "o_data"})
# --- 6. ports_detail consistency
ok = True; pnames = {b["id"]: ({p["name"] for p in b["ports_detail"]["inputs"]}, {p["name"] for p in b["ports_detail"]["outputs"]}) for b in js["blocks"]}
for e in js["edges"]:
    sb, sp = e["from"].split(".", 1); db, dp = e["to"].split(".", 1)
    comp = {"key_expand_step"}   # composite block: its inputs fan out to sub-blocks, its output comes from a sub-block
    ok &= (sb == "design port" or sp in pnames[sb][1] or (sb in comp and sp in pnames[sb][0])) and (db == "design port" or dp in pnames[db][0] or (db in comp and dp in pnames[db][1]))
check("edges: every endpoint is a described port", ok)
ok = True
for b in js["blocks"]:
    for side, key in (("upstream_blocks", "inputs"), ("downstream_blocks", "outputs")):
        want = {}
        for p in b["ports_detail"][key]:
            for c in p["connected_to"]:
                want.setdefault(c["block"], set()).add(p["name"])
        got = {x["block"]: set(x["signals"]) for x in b[side]}
        ok &= want == got and all(x["count"] == len(x["signals"]) for x in b[side])
    for p in b["ports_detail"]["inputs"] + b["ports_detail"]["outputs"]:
        ok &= all(k in p for k in ["name", "width", "kind", "clock", "edge", "storage", "latency_min_cycles", "latency_max_cycles", "latency_from", "connected_to", "valid_when", "note"])
    ok &= bool(b["function_detail"]) and hasattr(m, b["python"].split(":")[1].split(".")[0])
check("ports_detail / upstream / downstream / function_detail complete and consistent with edges for all 19 blocks", ok and len(js["blocks"]) == 19)
print("ALL PASS" if fails == 0 else f"{fails} FAILED")
sys.exit(1 if fails else 0)
