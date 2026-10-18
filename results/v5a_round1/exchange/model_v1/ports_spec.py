"""Port-level detail for model.json: ports (attributes), connections, function_detail, cli. Used by build_json.py."""
D = "design port"
CMB, REG = "combinational", "registered"
DV = lambda s: f"data-valid-with({s})"

# port: name -> (width, kind, storage, lat_min, lat_max, latency_from, valid_when, note)
def p(name, width, kind, storage, lmin, lmax, lfrom, valid, note=""):
    return dict(name=name, width=width, kind=kind, storage=storage, lmin=lmin, lmax=lmax, lfrom=lfrom, valid=valid, note=note)

PORTS = {
 "load_block": dict(
   ins=[p("i_data", 128, DV("i_start"), CMB, 0, 0, "design port i_data (wire)", "row 0 (start row)", "byte 0 = bits[127:120]")],
   outs=[p("state_in", 128, DV("i_start"), CMB, 0, 0, "i_data (same row)", "row 0; captured by state_reg at the start edge", "pure wiring, same bits; row n%4, col n//4")]),
 "state_reg": dict(
   ins=[p("state_in", 128, DV("i_start"), CMB, 0, 0, "load_block.state_in (wire)", "row 0 only"),
        p("state_next", 128, DV("round_cnt"), CMB, 0, 0, "round_mux.state_next (wire)", "rows with round_cnt = 1..11", "written at the edge that ends such a row"),
        p("load_sel", 1, "one-cycle pulse", CMB, 0, 0, "round_counter.start_accept (wire)", "row 0", "1 = take state_in; else take state_next when round_cnt != 0; else hold")],
   outs=[p("q", 128, "held", REG, 1, 1, "state_in / state_next (one clock edge)", "row 1 onward; plaintext when o_done = 1",
           "holds during key expansion and while idle (AA5). Row 1 = ciphertext (AA8)")]),
 "round_key_store": dict(
   ins=[p("rk0_in", 128, DV("upd_load"), CMB, 0, 0, "design port i_key (wire)", "row 0 of an update start", "byte 0 = MSB; i_key is 0 in later rows"),
        p("rk_next", 128, DV("key_cnt"), CMB, 0, 0, "key_expand_step.next_round_key (wire)", "key_cnt = 1..10", "written into rk[key_cnt]"),
        p("key_idx", 4, "level", CMB, 0, 0, "key_counter.key_cnt (wire)", "key_cnt = 1..10", "selects the entry written (n) and the entry read (n-1)"),
        p("rk0_load", 1, "one-cycle pulse", CMB, 0, 0, "key_counter.upd_load (wire)", "row 0 of an update start")],
   outs=[p("rk_prev", 128, DV("key_cnt"), REG, 0, 1, "key_idx (0, read mux) / rk_next (1, written at the edge)", "key_cnt = 1..10", "= rk[key_cnt-1]"),
         p("rk_all", 1408, "held", REG, 1, 1, "rk0_in / rk_next (one clock edge)", "rk[0] from row 1 of an update; rk[n] from row n+1; all valid when key_done = 1",
           "11 x 128 bit, rk[0] first (most significant) in the concatenation used by model_cli.py round_key_select; kept across operations (AA13)")]),
 "key_expand_step": dict(
   ins=[p("prev_round_key", 128, DV("key_cnt"), CMB, 0, 0, "round_key_store.rk_prev (wire)", "key_cnt = 1..10"),
        p("n", 4, "level", CMB, 0, 0, "key_counter.key_cnt (wire)", "key_cnt = 1..10", "Rcon index; hex digit")],
   outs=[p("next_round_key", 128, DV("key_cnt"), CMB, 0, 0, "prev_round_key, n (same row)", "key_cnt = 1..10", "stored by round_key_store at the end of the row (AA1)")]),
 "rot_word": dict(
   ins=[p("w3", 32, DV("key_cnt"), CMB, 0, 0, "key_expand_step.prev_round_key bytes 12..15 (wire)", "key_cnt = 1..10", "word 3 of the previous round key")],
   outs=[p("rot", 32, DV("key_cnt"), CMB, 0, 0, "w3", "key_cnt = 1..10")]),
 "sub_word": dict(
   ins=[p("rot", 32, DV("key_cnt"), CMB, 0, 0, "rot_word.rot (wire)", "key_cnt = 1..10")],
   outs=[p("sub", 32, DV("key_cnt"), CMB, 0, 0, "rot", "key_cnt = 1..10")]),
 "rcon_step": dict(
   ins=[p("sub", 32, DV("key_cnt"), CMB, 0, 0, "sub_word.sub (wire)", "key_cnt = 1..10"),
        p("n", 4, "level", CMB, 0, 0, "key_expand_step.n (wire)", "key_cnt = 1..10")],
   outs=[p("t", 32, DV("key_cnt"), CMB, 0, 0, "sub, n", "key_cnt = 1..10", "Rcon[n] XORed into byte 0 only")]),
 "word_xor_chain": dict(
   ins=[p("prev_round_key", 128, DV("key_cnt"), CMB, 0, 0, "key_expand_step.prev_round_key (wire)", "key_cnt = 1..10"),
        p("t", 32, DV("key_cnt"), CMB, 0, 0, "rcon_step.t (wire)", "key_cnt = 1..10")],
   outs=[p("next_round_key", 128, DV("key_cnt"), CMB, 0, 0, "prev_round_key, t", "key_cnt = 1..10", "serial XOR chain: w1' depends on w0' etc.")]),
 "round_key_select": dict(
   ins=[p("rk_all", 1408, "held", REG, 0, 0, "round_key_store.rk_all (wire from registers)", "all rk valid (key_done = 1)"),
        p("round_cnt", 4, "level", CMB, 0, 0, "round_counter.round_cnt (wire)", "round_cnt = 1..11")],
   outs=[p("round_key", 128, DV("round_cnt"), CMB, 0, 0, "round_cnt (same row)", "round_cnt = 1..11", "index: 1 -> 10; r -> 11-r (r = 2..11)")]),
 "add_round_key": dict(
   ins=[p("state", 128, DV("round_cnt"), CMB, 0, 0, "state_reg.q (round_cnt = 1) or inv_sub_bytes.state_out (round_cnt = 2..11) (wire)", "round_cnt = 1..11",
          "two sources; the choice is made by round_cnt = 1 (mux counted in round_mux)"),
        p("round_key", 128, DV("round_cnt"), CMB, 0, 0, "round_key_select.round_key (wire)", "round_cnt = 1..11")],
   outs=[p("state_out", 128, DV("round_cnt"), CMB, 0, 0, "state, round_key (same row)", "round_cnt = 1..11")]),
 "inv_shift_rows": dict(
   ins=[p("state", 128, DV("round_cnt"), CMB, 0, 0, "state_reg.q (wire)", "round_cnt = 2..11")],
   outs=[p("state_out", 128, DV("round_cnt"), CMB, 0, 0, "state", "round_cnt = 2..11")]),
 "inv_sub_bytes": dict(
   ins=[p("state", 128, DV("round_cnt"), CMB, 0, 0, "inv_shift_rows.state_out (wire)", "round_cnt = 2..11")],
   outs=[p("state_out", 128, DV("round_cnt"), CMB, 0, 0, "state", "round_cnt = 2..11")]),
 "inv_mix_columns": dict(
   ins=[p("state", 128, DV("round_cnt"), CMB, 0, 0, "add_round_key.state_out (wire)", "round_cnt = 2..10")],
   outs=[p("state_out", 128, DV("round_cnt"), CMB, 0, 0, "state", "round_cnt = 2..10", "not used in round_cnt 11 (bypassed)")]),
 "round_mux": dict(
   ins=[p("initial_path", 128, DV("round_cnt"), CMB, 0, 0, "add_round_key.state_out (wire)", "round_cnt = 1"),
        p("round_path", 128, DV("round_cnt"), CMB, 0, 0, "inv_mix_columns.state_out (wire)", "round_cnt = 2..10"),
        p("final_path", 128, DV("round_cnt"), CMB, 0, 0, "add_round_key.state_out (wire)", "round_cnt = 11"),
        p("round_cnt", 4, "level", CMB, 0, 0, "round_counter.round_cnt (wire)", "always")],
   outs=[p("state_next", 128, DV("round_cnt"), CMB, 0, 0, "inputs (same row)", "round_cnt = 1..11", "also drives the add_round_key.state input mux (round_cnt = 1: state_reg.q, else inv_sub_bytes)")]),
 "output_map": dict(
   ins=[p("q", 128, "held", REG, 0, 0, "state_reg.q (wire)", "always; meaningful when o_done = 1")],
   outs=[p("o_data", 128, "held", CMB, 0, 0, "q (same row)", "o_done = 1 (AA5)", "design port o_data; registered upstream (state_reg), so seen 1 clock after the last round step")]),
 "key_counter": dict(
   ins=[p("i_start", 1, "one-cycle pulse", CMB, 0, 0, "design port i_start (wire)", "row 0"),
        p("i_update_key", 1, "level", CMB, 0, 0, "design port i_update_key (wire)", "row 0 only (AA10)"),
        p("round_cnt", 4, "level", CMB, 0, 0, "round_counter.round_cnt (wire)", "always", "idle test: key_cnt = 0 and round_cnt = 0")],
   outs=[p("key_cnt", 4, "level", REG, 1, 1, "i_start & i_update_key & idle, or itself (one clock edge)", "rows 1..10 of an update (AA1)", "0 otherwise"),
         p("upd_load", 1, "one-cycle pulse", CMB, 0, 0, "i_start, i_update_key, key_cnt, round_cnt (same row)", "row 0 of an update start", "= idle & i_start & i_update_key")]),
 "round_counter": dict(
   ins=[p("i_start", 1, "one-cycle pulse", CMB, 0, 0, "design port i_start (wire)", "row 0"),
        p("i_update_key", 1, "level", CMB, 0, 0, "design port i_update_key (wire)", "row 0 only (AA10)"),
        p("key_cnt", 4, "level", CMB, 0, 0, "key_counter.key_cnt (wire)", "always", "== 10 -> start decrypt; == 0 part of idle test")],
   outs=[p("round_cnt", 4, "level", REG, 1, 1, "start (no update) / key_cnt = 10 / itself (one clock edge)", "no update: rows 1..11; update: rows 11..21 (AA2, AA3)", "0 otherwise"),
         p("start_accept", 1, "one-cycle pulse", CMB, 0, 0, "i_start, key_cnt, round_cnt (same row)", "row 0", "= idle & i_start")]),
 "done_gen": dict(
   ins=[p("round_cnt", 4, "level", CMB, 0, 0, "round_counter.round_cnt (wire)", "always", "== 11 -> pulse next row")],
   outs=[p("o_done", 1, "one-cycle pulse", REG, 1, 1, "round_cnt == 11 (one clock edge)", "no update: row 12; update: row 22 (AA3, AA4)")]),
 "key_done_flag": dict(
   ins=[p("upd_load", 1, "one-cycle pulse", CMB, 0, 0, "key_counter.upd_load (wire)", "row 0 of an update start"),
        p("key_cnt", 4, "level", CMB, 0, 0, "key_counter.key_cnt (wire)", "always", "== 10 -> set")],
   outs=[p("key_done", 1, "level", REG, 1, 1, "upd_load / key_cnt == 10 (one clock edge)", "0 from row 1 of an update until row 10; 1 from row 11 (AA12)", "no consumer in the model: observation signal; may not exist in the RTL")]),
}

# connections: (src_block, src_port, dst_block, dst_port, when)
C = [
 (D, "i_data", "load_block", "i_data", ""), ("load_block", "state_in", "state_reg", "state_in", ""),
 (D, "i_start", "key_counter", "i_start", ""), (D, "i_update_key", "key_counter", "i_update_key", ""),
 (D, "i_start", "round_counter", "i_start", ""), (D, "i_update_key", "round_counter", "i_update_key", ""),
 (D, "i_key", "round_key_store", "rk0_in", "i_update_key = 1 at start"),
 ("key_counter", "key_cnt", "round_counter", "key_cnt", ""), ("round_counter", "round_cnt", "key_counter", "round_cnt", ""),
 ("key_counter", "key_cnt", "round_key_store", "key_idx", ""), ("key_counter", "key_cnt", "key_expand_step", "n", ""),
 ("key_counter", "key_cnt", "key_done_flag", "key_cnt", ""), ("key_counter", "upd_load", "key_done_flag", "upd_load", ""),
 ("key_counter", "upd_load", "round_key_store", "rk0_load", ""),
 ("round_counter", "start_accept", "state_reg", "load_sel", ""),
 ("round_counter", "round_cnt", "round_key_select", "round_cnt", ""), ("round_counter", "round_cnt", "round_mux", "round_cnt", ""),
 ("round_counter", "round_cnt", "done_gen", "round_cnt", ""), ("done_gen", "o_done", D, "o_done", ""),
 ("round_key_store", "rk_prev", "key_expand_step", "prev_round_key", ""),
 ("key_expand_step", "prev_round_key", "rot_word", "w3", "bytes 12..15 of the 128-bit input"),
 ("key_expand_step", "prev_round_key", "word_xor_chain", "prev_round_key", ""),
 ("key_expand_step", "n", "rcon_step", "n", ""),
 ("rot_word", "rot", "sub_word", "rot", ""), ("sub_word", "sub", "rcon_step", "sub", ""),
 ("rcon_step", "t", "word_xor_chain", "t", ""),
 ("word_xor_chain", "next_round_key", "key_expand_step", "next_round_key", "composite output"),
 ("key_expand_step", "next_round_key", "round_key_store", "rk_next", ""),
 ("round_key_store", "rk_all", "round_key_select", "rk_all", ""),
 ("round_key_select", "round_key", "add_round_key", "round_key", ""),
 ("state_reg", "q", "add_round_key", "state", "round_cnt = 1"), ("state_reg", "q", "inv_shift_rows", "state", "round_cnt = 2..11"),
 ("state_reg", "q", "output_map", "q", ""),
 ("inv_shift_rows", "state_out", "inv_sub_bytes", "state", ""),
 ("inv_sub_bytes", "state_out", "add_round_key", "state", "round_cnt = 2..11"),
 ("add_round_key", "state_out", "inv_mix_columns", "state", "round_cnt = 2..10"),
 ("add_round_key", "state_out", "round_mux", "initial_path", "round_cnt = 1"),
 ("add_round_key", "state_out", "round_mux", "final_path", "round_cnt = 11"),
 ("inv_mix_columns", "state_out", "round_mux", "round_path", ""),
 ("round_mux", "state_next", "state_reg", "state_next", ""),
 ("output_map", "o_data", D, "o_data", ""),
]

FD = {
 "load_block": "model.py:load_block(i_data:int128) -> list of 16 bytes. byte n = i_data[127-8n -: 8] (n = 0..15), state row n%4, column n//4. CLI: model_cli.py block load_block <i_data 32 hex> -> 32 hex, identical digits (pure wiring).",
 "state_reg": "model.py:Top.state (16 bytes). Per edge: load_sel -> load_block output; else round_cnt != 0 -> round_step(...) = state_next; else hold. Reset 0. Not a pure function; no CLI.",
 "round_key_store": "model.py:Top.rk (11 lists of 16 bytes). Per edge: rk0_load -> rk[0] = bytes of i_key (byte 0 = MSB); key_cnt = n != 0 -> rk[n] = next_round_key(rk[n-1], n). Not pure; no CLI.",
 "key_expand_step": "model.py:next_round_key(prev: 16 bytes, n: 1..10) -> 16 bytes. t = RconXor(SubWord(RotWord(prev[12:16])), n); w0 = prev[0:4]^t; w1 = prev[4:8]^w0; w2 = prev[8:12]^w1; w3 = prev[12:16]^w2; output w0||w1||w2||w3, each word byte 0 first. CLI: key_expand_step <prev_round_key 32 hex> <n hex> -> 32 hex.",
 "rot_word": "model.py:rot_word(w: 4 bytes) -> [w1,w2,w3,w0]. CLI: rot_word <w3 8 hex> -> 8 hex. Example 09cf4f3c -> cf4f3c09.",
 "sub_word": "model.py:sub_word(w: 4 bytes) -> forward S-box per byte. CLI: sub_word <8 hex> -> 8 hex. Example cf4f3c09 -> 8a84eb01.",
 "rcon_step": "model.py:rcon_xor(w: 4 bytes, n: 1..10) -> w with byte 0 XORed with Rcon[n] (01 02 04 08 10 20 40 80 1b 36); bytes 1..3 unchanged. CLI: rcon_step <sub 8 hex> <n hex> -> 8 hex.",
 "word_xor_chain": "model.py:next_round_key (second half) -> w0 = prev[0:4]^t; w1 = prev[4:8]^w0; w2 = prev[8:12]^w1; w3 = prev[12:16]^w2, output 16 bytes w0||w1||w2||w3. CLI: word_xor_chain <prev_round_key 32 hex> <t 8 hex> -> 32 hex.",
 "round_key_select": "model.py:round_key_index(r: 1..11) -> index into rk: 1 -> 10; r in 2..11 -> 11-r. Output = rk[index] (16 bytes). CLI: round_key_select <rk_all 352 hex = rk[0]||rk[1]||...||rk[10], rk[0] most significant> <round_cnt hex> -> 32 hex.",
 "add_round_key": "model.py:add_round_key(state: 16 bytes, round_key: 16 bytes) -> byte-wise XOR (byte n with byte n; both row n%4, col n//4). CLI: add_round_key <state 32 hex> <round_key 32 hex> -> 32 hex.",
 "inv_shift_rows": "model.py:inv_shift_rows(state: 16 bytes) -> out[row r, col c] = in[row r, col (c-r) mod 4]; byte index 4*c + r. Row 0 unchanged. CLI: inv_shift_rows <state 32 hex> -> 32 hex. Example 000102..0f -> 000d0a0704010e0b0805020f0c090603.",
 "inv_sub_bytes": "model.py:inv_sub_bytes(state: 16 bytes) -> inverse S-box per byte (position unchanged). CLI: inv_sub_bytes <state 32 hex> -> 32 hex.",
 "inv_mix_columns": "model.py:inv_mix_columns(state: 16 bytes) -> per column c (bytes 4c..4c+3 = rows 0..3): out_r = 0E*a_r ^ ... with matrix rows [0E 0B 0D 09; 09 0E 0B 0D; 0D 09 0E 0B; 0B 0D 09 0E] applied to (a0,a1,a2,a3), GF(2^8) mod 0x11B. CLI: inv_mix_columns <state 32 hex> -> 32 hex.",
 "round_mux": "model.py:round_step(state, rk, r) selects: r = 1 -> add_round_key(state, rk[10]); r = 2..10 -> inv_mix_columns(add_round_key(inv_sub_bytes(inv_shift_rows(state)), rk[11-r])); r = 11 -> add_round_key(inv_sub_bytes(inv_shift_rows(state)), rk[0]). CLI (selection only): round_mux <initial_path 32 hex> <round_path 32 hex> <final_path 32 hex> <round_cnt hex> -> the path chosen by round_cnt (1: initial, 2..10: round, 11: final), 32 hex.",
 "output_map": "model.py:output_map(state: 16 bytes) -> int128; o_data[127-8n -: 8] = byte n. CLI: output_map <q 32 hex> -> 32 hex, identical digits.",
 "key_counter": "model.py:next_key_cnt(key_cnt, round_cnt, i_start, i_update_key) -> next key_cnt: key_cnt != 0 -> 0 if 10 else +1; else 1 if round_cnt == 0 and i_start and i_update_key else 0. upd_load = idle & i_start & i_update_key. Not in CLI (sequential).",
 "round_counter": "model.py:next_round_cnt(key_cnt, round_cnt, i_start, i_update_key) -> next round_cnt: key_cnt != 0 -> 1 if key_cnt == 10 else 0; round_cnt != 0 -> 0 if 11 else +1; else 1 if i_start and not i_update_key else 0. start_accept = idle & i_start. Not in CLI (sequential).",
 "done_gen": "model.py:next_done(round_cnt) -> 1 if round_cnt == 11 else 0 (registered into o_done). Not in CLI.",
 "key_done_flag": "model.py:next_key_done(key_done, key_cnt, upd_load) -> 0 if upd_load; 1 if key_cnt == 10; else unchanged. Not in CLI.",
}
PY = {"state_reg": "model.py:Top.state", "round_key_store": "model.py:Top.rk", "round_key_select": "model.py:round_key_index",
      "round_mux": "model.py:round_step", "key_counter": "model.py:next_key_cnt", "round_counter": "model.py:next_round_cnt",
      "done_gen": "model.py:next_done", "key_done_flag": "model.py:next_key_done", "word_xor_chain": "model.py:next_round_key",
      "rcon_step": "model.py:rcon_xor"}

def apply(blocks):
    srcs = {}
    for sb, sp, db, dp, w in C:
        srcs.setdefault((sb, sp, "out"), []).append((db, dp, w))
        srcs.setdefault((db, dp, "in"), []).append((sb, sp, w))
    total = 0
    for b in blocks:
        spec = PORTS[b["id"]]
        pd = {"inputs": [], "outputs": []}
        for side, key, lst in (("in", "inputs", spec["ins"]), ("out", "outputs", spec["outs"])):
            for q in lst:
                conn = []
                for blk, port, w in srcs.get((b["id"], q["name"], side), []):
                    c = {"block": blk, "port": port}
                    if w:
                        c["when"] = w
                    conn.append(c)
                e = {"name": q["name"], "width": q["width"], "kind": q["kind"],
                     "clock": "clk" if q["storage"] == REG or q["name"] in ("i_start",) and False else ("clk" if q["storage"] == REG else "none (combinational)"),
                     "edge": "pos" if q["storage"] == REG else "n/a", "storage": q["storage"],
                     "latency_min_cycles": q["lmin"], "latency_max_cycles": q["lmax"],
                     "latency_from": q["lfrom"], "connected_to": conn, "valid_when": q["valid"], "note": q["note"]}
                if not conn:
                    e["note"] = (e["note"] + " ").lstrip() + "(no consumer in the model)"
                pd[key].append(e); total += 1
        b["ports_detail"] = pd
        b["inputs"] = [{"name": q["name"], "width": q["width"]} for q in spec["ins"]]
        b["outputs"] = [{"name": q["name"], "width": q["width"]} for q in spec["outs"]]
        for side, key in (("upstream_blocks", "inputs"), ("downstream_blocks", "outputs")):
            d = {}
            for q in pd[key]:
                for c in q["connected_to"]:
                    d.setdefault(c["block"], set()).add(c["port"] if key == "outputs" else None)
            # signals = names of the signals on the link: ports of this block (inputs) or of this block (outputs)
            lst = []
            for blk in d:
                names = sorted({q["name"] for q in pd[key] if any(c["block"] == blk for c in q["connected_to"])})
                lst.append({"block": blk, "signals": names, "count": len(names)})
            b[side] = lst
        b["function_detail"] = FD[b["id"]]
        b["python"] = PY.get(b["id"], b["python"])
    edges = [{"from": f"{sb}.{sp}", "to": f"{db}.{dp}", **({"when": w} if w else {})} for sb, sp, db, dp, w in C]
    return total, edges
