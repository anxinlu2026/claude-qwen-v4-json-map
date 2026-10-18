"""Builds model.json and assumptions_arch.json (hand-written content; the schedule comes from model.py)."""
import json
import model as m
import ports_spec

KEY = 0x2b7e151628aed2a6abf7158809cf4f3c
CT = 0x3925841d02dc09fbdc118597196a0b32
PT = 0x3243f6a8885a308d313198a2e0370734

def sched(update):
    rows, out = m.run_case(update, KEY, CT)
    keys = ["i_start", "i_update_key", "key_cnt", "round", "key_done", "o_done"]
    s = {k: [r[k] for r in rows] for k in keys}
    s["o_data_valid"] = [r["o_done"] for r in rows]
    s["rows"] = len(rows)
    return s

def port(name, d, w, role, **kw):
    return dict(name=name, dir=d, width=w, role=role, **kw)

interface = [
    port("clk", "in", 1, "clock", edge="pos", function="Clock; all registers change on the rising edge. TB period 10 time units (clk toggles every 5)."),
    port("rst_async_n", "in", 1, "reset", level="low", sync="asynchronous",
         timing="TB: low for 2 time units at start; cocotb: low for one clock, then high. Asserting it clears every register.",
         function="Asynchronous active-low reset: idle, counters 0, key_done 0, state 0 so o_data = 0, o_done = 0 (AA6)."),
    port("i_update_key", "in", 1, "control", level="high",
         timing="level; only looked at in the row where i_start = 1; TB and cocotb drive it 0 in all later rows, so it must not be sampled again after the start row (AA10)",
         function="1 together with i_start: take i_key as the new cipher key, expand it first (10 clocks), then decrypt. 0 together with i_start: reuse the stored expanded key."),
    port("i_key", "in", 128, "data", layout="byte 0 = bits[127:120] = first key byte (W[0] = bits[127:96]); FIPS 197 order",
         timing="valid only in the start row (TB/cocotb set it to 0 right after); must be captured at the start edge when i_update_key = 1; ignored otherwise",
         function="128-bit cipher key."),
    port("i_start", "in", 1, "control", level="high",
         timing="one-cycle pulse (TB: set at negedge, cleared at next negedge = sampled at exactly one rising edge; cocotb: one clock); sampled at the rising edge; ignored while busy (AA7)",
         function="Starts one decryption of the block on i_data."),
    port("i_data", "in", 128, "data", layout="byte n = bits[127-8n:120-8n] = state row n%4, column n//4 (TB comment: 39 25 84 1d is column 0)",
         timing="valid only in the start row; TB/cocotb set it to 0 right after; must be latched at the start edge (AA8)",
         function="128-bit ciphertext block."),
    port("o_done", "out", 1, "control", level="high", registered=True,
         timing="0 in the row after the start row (a stale 1 would make the cocotb loop compare too early); then 1 for exactly one row when o_data holds the plaintext; 0 again (AA4). The TB waits for a rising edge of o_done, so it must be 0 before the pulse.",
         function="Result valid."),
    port("o_data", "out", 128, "data", registered=True, layout="same byte order as i_data",
         timing="correct plaintext in the row where o_done = 1 (TB reads it at the negedge inside that row; cocotb reads it in the row it sees o_done = 1); after reset 0 (AA5, AA6); value in other rows not specified (AA5)",
         function="128-bit plaintext block."),
]
params = {"NBW_KEY": 128, "NBW_DATA": 128}

def blk(id, kind, ins, outs, ttype, valid, py, fn, **kw):
    d = dict(id=id, kind=kind, inputs=ins, outputs=outs, timing=dict(type=ttype, valid_when=valid), python=py, function=fn)
    d.update(kw)
    return d

S = lambda n="state", w=128: dict(name=n, width=w, layout="byte n = row n%4, col n//4; byte 0 = MSB")
RK = lambda n="round_key": dict(name=n, width=128, layout="word j = bytes 4j..4j+3 = column j; word 0 = MSB")
W = lambda n: dict(name=n, width=32, layout="byte 0 = MSB")

blocks = [
    blk("load_block", "datapath", [dict(name="i_data", width=128, layout="byte 0 = MSB")], [S("state_in")],
        "combinational", "always (captured into state_reg at the start edge)", "model.py:load_block",
        "Maps port i_data to the 4x4 state: byte n = i_data[127-8n -: 8], row n%4, column n//4. Pure wiring."),
    blk("state_reg", "register", [S("state_in"), S("state_next")], [S("q")],
        "registered", "q holds: ciphertext after start edge; then result of the previous step; plaintext after round 11",
        "model.py:Top.state",
        "128-bit state. Loads i_data at the start edge (idle & i_start); holds during key expansion (key_cnt != 0); "
        "updates once per clock while round_cnt = 1..11; holds when idle. Reset 0.",
        load_when="idle & i_start", hold_when="key expansion or idle (no start)"),
    blk("round_key_store", "register", [RK("rk0_in"), RK("rk_next"), dict(name="key_idx", width=4)], [RK("rk[0..10]")],
        "registered", "rk[0] valid from the start edge of an update; rk[n] valid from the end of key step n; all 11 valid when key_done = 1",
        "model.py:Top.rk",
        "11 x 128-bit expanded key, kept across operations (stored key reused when i_update_key = 0). "
        "rk[0] <= i_key at the start edge when i_update_key = 1; rk[n] <= next_round_key(rk[n-1], n) in key step n (n = 1..10)."),
    blk("key_expand_step", "datapath", [RK("prev_round_key"), dict(name="n", width=4, note="1..10 = key_cnt")], [RK("next_round_key")],
        "combinational", "key_cnt = 1..10", "model.py:next_round_key",
        "One step of the key schedule: round key n-1 -> n. t = Rcon(n) xor' SubWord(RotWord(w3)); w0' = w0^t; w1' = w1^w0'; w2' = w2^w1'; w3' = w3^w2'. "
        "(Equivalent to W[i] rules of the spec for i = 4n..4n+3.)",
        sub_blocks=["rot_word", "sub_word", "rcon_step", "word_xor_chain"]),
    blk("rot_word", "datapath", [W("w3")], [W("rot")], "combinational", "always", "model.py:rot_word",
        "[b0,b1,b2,b3] -> [b1,b2,b3,b0] (one byte left rotation)."),
    blk("sub_word", "datapath", [W("rot")], [W("sub")], "combinational", "always", "model.py:sub_word",
        "Apply the forward S-box to each byte (module sbox, already tested per the task text)."),
    blk("rcon_step", "datapath", [W("sub"), dict(name="n", width=4)], [W("t")], "combinational", "always", "model.py:rcon_xor",
        "XOR Rcon[n] into byte 0 (the most significant byte) of the word. Rcon[1..10] = 01 02 04 08 10 20 40 80 1b 36 (already tested per the task text)."),
    blk("word_xor_chain", "datapath", [RK("prev_round_key"), W("t")], [RK("next_round_key")], "combinational", "always", "model.py:next_round_key",
        "w0' = w0^t, w1' = w1^w0', w2' = w2^w1', w3' = w3^w2' (serial XOR chain across the four words)."),
    blk("round_key_select", "datapath", [dict(name="rk[0..10]", width=1408), dict(name="round_cnt", width=4)], [RK("round_key")],
        "combinational", "round_cnt = 1..11", "model.py:Top.step (index 11 - round_cnt, initial step uses 10)",
        "Decryption uses round keys in reverse: round_cnt 1 -> rk[10]; round_cnt r = 2..10 -> rk[11-r] (9..1); round_cnt 11 -> rk[0]. "
        "Note rounds 1..10 of the spec = round_cnt 2..11."),
    blk("add_round_key", "datapath", [S(), RK()], [S("state_out")], "combinational", "round_cnt = 1..11", "model.py:add_round_key",
        "Byte-wise XOR of state and round key (same byte layout)."),
    blk("inv_shift_rows", "datapath", [S()], [S("state_out")], "combinational", "round_cnt = 2..11", "model.py:inv_shift_rows",
        "Row r rotated right by r columns: out[r][c] = in[r][(c - r) mod 4]. Row 0 unchanged. Not used in round_cnt 1 (initial AddRoundKey)."),
    blk("inv_sub_bytes", "datapath", [S()], [S("state_out")], "combinational", "round_cnt = 2..11", "model.py:inv_sub_bytes",
        "Inverse S-box on each of the 16 bytes (module inv_sbox, already tested)."),
    blk("inv_mix_columns", "datapath", [S()], [S("state_out")], "combinational", "round_cnt = 2..10 only (bypassed in round_cnt 11)", "model.py:inv_mix_columns",
        "Each column multiplied by the circulant matrix [0E 0B 0D 09; 09 0E 0B 0D; 0D 09 0E 0B; 0B 0D 09 0E] in GF(2^8), polynomial 0x11B. "
        "Output after AddRoundKey (order InvShiftRows, InvSubBytes, AddRoundKey, InvMixColumns)."),
    blk("round_mux", "datapath", [S("initial_path"), S("round_path"), S("final_path")], [S("state_next")], "combinational", "round_cnt != 0",
        "model.py:Top.step",
        "Selects state_next: round_cnt 1 -> ARK(state, rk[10]) (no shift/sub/mix); round_cnt 2..10 -> InvMixColumns(ARK(InvSub(InvShift(state)), key)); "
        "round_cnt 11 -> ARK(InvSub(InvShift(state)), rk[0]) (no InvMixColumns)."),
    blk("output_map", "datapath", [S("q")], [dict(name="o_data", width=128, layout="byte 0 = MSB")], "combinational (wiring)", "o_done = 1", "model.py:output_map",
        "o_data = state_reg.q, byte n -> o_data[127-8n -: 8]. Inverse of load_block. No extra register (AA5)."),
    blk("key_counter", "control", [dict(name="start&update", width=1)], [dict(name="key_cnt", width=4)], "registered", "always", "model.py:Top.key_cnt",
        "0 = no key expansion running; start edge with i_update_key -> 1; counts 1..10 one per clock; after the clock with key_cnt = 10 returns to 0 and key_done becomes 1."),
    blk("round_counter", "control", [dict(name="start", width=1), dict(name="key_cnt_last", width=1)], [dict(name="round_cnt", width=4)], "registered", "always",
        "model.py:Top.round_cnt",
        "0 = idle; set to 1 at the start edge if no key update, or at the end of key step 10 if key update; counts 1..11 one per clock; returns to 0 after the clock with 11."),
    blk("done_gen", "control", [dict(name="round_cnt_eq_11", width=1)], [dict(name="o_done", width=1)], "registered", "always", "model.py:Top.done",
        "o_done <= 1 at the edge that ends round_cnt = 11, else 0. One-cycle pulse (AA4)."),
    blk("key_done_flag", "control", [dict(name="start&update", width=1), dict(name="key_cnt_eq_10", width=1)], [dict(name="key_done", width=1)], "registered", "always",
        "model.py:Top.key_done",
        "0 after reset and from the start edge of an update; 1 from the end of key step 10. Stays 1 across operations without update. "
        "Internal; not a port; the name is the architect's (AA12)."),
]

edges = [
    ("i_data", "load_block.i_data"), ("load_block.state_in", "state_reg.state_in"),
    ("state_reg.q", "output_map.q"), ("output_map.o_data", "o_data"),
    ("state_reg.q", "add_round_key.state [initial: round_cnt 1]"), ("state_reg.q", "inv_shift_rows.state"),
    ("inv_shift_rows.state_out", "inv_sub_bytes.state"), ("inv_sub_bytes.state_out", "add_round_key.state [rounds]"),
    ("round_key_select.round_key", "add_round_key.round_key"),
    ("add_round_key.state_out", "inv_mix_columns.state [round_cnt 2..10]"),
    ("add_round_key.state_out", "round_mux (initial_path round_cnt 1 / final_path round_cnt 11)"),
    ("inv_mix_columns.state_out", "round_mux.round_path"), ("round_mux.state_next", "state_reg.state_next"),
    ("i_key", "round_key_store.rk0_in [start & update]"),
    ("round_key_store.rk[n-1]", "key_expand_step.prev_round_key"),
    ("key_counter.key_cnt", "key_expand_step.n"), ("key_counter.key_cnt", "round_key_store.key_idx"),
    ("key_expand_step.next_round_key", "round_key_store.rk_next"),
    ("key_expand_step.prev_round_key.w3", "rot_word.w3"), ("rot_word.rot", "sub_word.rot"),
    ("sub_word.sub", "rcon_step.sub"), ("rcon_step.t", "word_xor_chain.t"),
    ("round_key_store.rk[0..10]", "round_key_select"), ("round_counter.round_cnt", "round_key_select.round_cnt"),
    ("round_counter.round_cnt", "round_mux"), ("round_counter.round_cnt", "done_gen"),
    ("i_start & i_update_key", "key_counter"), ("i_start & !i_update_key", "round_counter"),
    ("key_counter (key_cnt = 10)", "round_counter"), ("key_counter (key_cnt = 10)", "key_done_flag"),
    ("done_gen.o_done", "o_done"),
]
edges = [dict(**{"from": a, "to": b}) for a, b in edges]

round_table = [dict(round_cnt=1, spec_step="initial AddRoundKey", key="rk[10]", ops="ARK")]
for r in range(2, 11):
    round_table.append(dict(round_cnt=r, spec_step=f"decryption round {r-1} of 10", key=f"rk[{11-r}]", ops="InvShiftRows, InvSubBytes, AddRoundKey, InvMixColumns"))
round_table.append(dict(round_cnt=11, spec_step="final round 10", key="rk[0]", ops="InvShiftRows, InvSubBytes, AddRoundKey"))

control = {
    "idle_definition": "key_cnt = 0 and round_cnt = 0. A start is accepted only when idle (also in the row where o_done = 1) (AA7).",
    "state_variables": {
        "key_cnt": "0, 1..10; step counter of the key expansion; value n = the clock in which round key n is computed and stored",
        "round_cnt": "0 idle, 1..11; value r = the clock in which step r of the table below is applied",
        "key_done": "1 when the stored expanded key is valid",
        "o_done": "registered one-cycle pulse"},
    "events": [
        dict(name="reset", when="rst_async_n = 0", effect="key_cnt = round_cnt = 0; key_done = 0; o_done = 0; state_reg = 0; rk stores 0 (AA6)"),
        dict(name="start_with_update", when="idle & i_start & i_update_key",
             effect="state_reg <= i_data; rk[0] <= i_key; key_done <= 0; key_cnt <= 1 (round_cnt stays 0)"),
        dict(name="start_without_update", when="idle & i_start & !i_update_key",
             effect="state_reg <= i_data; rk unchanged; round_cnt <= 1"),
        dict(name="key_step", when="key_cnt = n, n = 1..9", effect="rk[n] <= next_round_key(rk[n-1], n); key_cnt <= n+1; state_reg holds"),
        dict(name="key_step_last", when="key_cnt = 10", effect="rk[10] <= next_round_key(rk[9], 10); key_cnt <= 0; key_done <= 1; round_cnt <= 1"),
        dict(name="round_step", when="round_cnt = r, r = 1..10", effect="state_reg <= step(r) per round_table; round_cnt <= r+1"),
        dict(name="round_last", when="round_cnt = 11", effect="state_reg <= final round result; round_cnt <= 0; o_done <= 1 (for the next row only)"),
        dict(name="done_clear", when="o_done = 1", effect="o_done <= 0 at the next edge (pulse); state_reg keeps the plaintext until the next start")],
    "round_table": round_table,
    "update_flow": "start row 0 -> rows 1..10 key_cnt = 1..10 (round keys 1..10) -> rows 11..21 round_cnt = 1..11 -> row 22 o_done = 1 with o_data = plaintext. All counts follow from AA1-AA3.",
    "no_update_flow": "start row 0 -> rows 1..11 round_cnt = 1..11 -> row 12 o_done = 1 with o_data = plaintext.",
    "serial_rule": "From the task text: the key expansion runs first, only then decryption steps start; decryption never overlaps with key steps. key_done = 1 is a precondition for round_cnt = 1.",
    "o_done_rule": "o_done = 1 only in the row after the clock with round_cnt = 11; never during key expansion (spec: not before the decryption is complete).",
    "remember_across_cycles": [
        dict(what="i_data (as state_reg)", why="TB and cocotb drive i_data = 0 from the row after start; the block must be latched at the start edge"),
        dict(what="i_key (as rk[0]) when i_update_key = 1", why="i_key = 0 from the row after start; needed for all 10 key steps"),
        dict(what="the decision 'update or not' (as key_cnt vs round_cnt, or an explicit flag)", why="i_update_key = 0 in the rows after start (TB and cocotb clear it), so the flow cannot sample it again"),
        dict(what="expanded key rk[0..10] across operations", why="a later start with i_update_key = 0 must reuse it; cocotb picks update_key at random per run"),
        dict(what="busy (key_cnt != 0 or round_cnt != 0)", why="start is a one-cycle pulse and must not restart a running operation (AA7)")],
    "per_case": {"update": "start_with_update, 10 x key_step, 11 x round_step, o_done", "no_update": "start_without_update, 11 x round_step, o_done"},
}

model = {
    "design": "aes128_decrypt", "parameters": params,
    "source_note": "Written from the task text, tb_aes128_dec.sv, test_aes128_decrypt.py, FIPS 197 and the library model; RTL not read. Items marked AAn are in assumptions_arch.json.",
    "byte_layout": "128-bit value: byte n = bits[127-8n : 120-8n]; state row = n%4, column = n//4; round key word j = bytes 4j..4j+3. Verified by the testbench vector (key 2b7e..., ct 3925..., pt 3243...).",
    "interface": interface, "blocks": blocks, "edges": edges, "control": control,
    "schedule": {
        "note": "Row t = values seen during clock cycle t. Row 0 = the row in which i_start = 1 is presented (sampled at the edge that ends row 0). "
                "i_start/i_update_key show the inputs of that row. key_cnt/round/key_done/o_done are register values during the row. "
                "Spec-fixed: o_done = 0 in row 1 and 1 only when o_data is the plaintext (TB/cocotb). Everything else in the table depends on AA1-AA4 (row counts) and AA6 (key_done initial value).",
        "cases": [
            dict(case="update", scenario="TB Simple_test(1) right after reset", **sched(1),
                 fixed_by_spec=["i_start", "i_update_key", "o_done[1]=0", "o_done at last row =1 with correct o_data"],
                 depends_on={"rows 1..10 key_cnt": "AA1", "rows 11..21 round": "AA2, AA3", "row 22 o_done": "AA1-AA4", "key_done initial 0": "AA6, AA12"}),
            dict(case="no_update", scenario="TB Simple_test(0) after an update run (stored key valid)", **{k: v for k, v in sched(0).items()},
                 fixed_by_spec=["i_start", "i_update_key", "o_done[1]=0", "o_done at last row =1 with correct o_data"],
                 depends_on={"rows 1..11 round": "AA2, AA3", "row 12 o_done": "AA2-AA4", "key_done=1 throughout": "AA12"}),
        ]},
}

assumptions = [
    dict(id="AA1", subject="key expansion length", value="10 clocks, one round key per clock (key_cnt 1..10), the first in the row after the start row",
         reason="Spec only says the expansion runs serially before decryption; a serial design with one 4-word step per clock gives 10 steps. Spec does not give a count.",
         check=dict(signal="key step counter / round_key_store writes", rows="update case rows 1..10; first decrypt step in row 11")),
    dict(id="AA2", subject="initial AddRoundKey", value="a separate clock (round_cnt = 1) with rk[10]; no InvShiftRows/InvSubBytes in it",
         reason="Spec lists it as its own step ('Initial step'); one clock per step is the simplest serial reading.",
         check=dict(signal="state register after first decrypt clock", rows="update row 12 / no-update row 2 equals ct ^ rk[10]")),
    dict(id="AA3", subject="one clock per decryption round, total latency", value="rounds 1..9 and the final round take one clock each; o_done row = 22 (update) / 12 (no update), counted from the start row = 0",
         reason="Not fixed by the spec; the TB/cocotb accept any latency (wait for o_done). Chosen as the minimum for a registered, serial design.",
         check=dict(signal="o_done", rows="row 22 (update), row 12 (no update); compare the round counter row by row")),
    dict(id="AA4", subject="o_done shape", value="registered one-cycle pulse; 0 in the row after the start row; 0 again in the row after it",
         reason="TB waits for a rising edge of o_done, and cocotb stops at the first sampled 1; a stale 1 would break both. A held-until-next-start o_done would also pass if cleared by the start edge; pulse chosen.",
         check=dict(signal="o_done", rows="rows 1 and done+1 are 0; exactly one row is 1")),
    dict(id="AA5", subject="o_data when o_done = 0", value="o_data is the state register directly (no separate output register); intermediate values are visible while busy; 0 after reset",
         reason="Spec fixes only o_data when o_done = 1 and (cocotb) after reset, where the library model starts with decrypted_data presumably 0 (the library harness_library is not visible; assumed 0).",
         check=dict(signal="o_data", rows="row after reset = 0; row with o_done = 1 = plaintext; other rows free")),
    dict(id="AA6", subject="reset values", value="all registers 0: key_cnt, round_cnt, o_done, key_done, state, stored round keys; reset also forgets the stored key",
         reason="cocotb resets 4 times and always starts the first run with update_key = 1, so the stored key after reset is never used; the spec says nothing else.",
         check=dict(signal="all registers", rows="row after rst_async_n goes high")),
    dict(id="AA7", subject="start while busy / in the done row", value="start while key_cnt != 0 or round_cnt != 0 is ignored; start in the o_done row is accepted (idle then)",
         reason="Not stated. cocotb starts the next run in the row after o_done has been seen; TB starts at least one row later. Neither starts while busy.",
         check=dict(signal="i_start", rows="not exercised by TB/cocotb; only check the design does not restart a running operation if this is tested")),
    dict(id="AA8", subject="capture of i_data and i_key", value="both captured at the start edge (i_data into state_reg, i_key into rk[0] when i_update_key = 1)",
         reason="TB and cocotb set both to 0 in the row after start, so the design must have stored them.",
         check=dict(signal="state_reg, rk[0]", rows="row 1 equals the ciphertext (state) and the key (rk[0], update case)")),
    dict(id="AA9", subject="start without update right after reset", value="not defined; model uses rk = 0 (key 0 not expanded)",
         reason="Spec silent; never exercised (first run after every reset is update = 1).",
         check=dict(signal="-", rows="not checked")),
    dict(id="AA10", subject="i_update_key sampling", value="looked at only in the start row (start_with_update vs start_without_update); never remembered beyond that except through key_cnt/round_cnt",
         reason="TB and cocotb clear it in the row after start, as the task text's own prompt lists it as the start modifier ('asserted by i_update_key and i_start').",
         check=dict(signal="i_update_key and the signal that selects key expansion", rows="update case rows 1..10 (i_update_key = 0 there, expansion must still run)")),
    dict(id="AA11", subject="round key order in decryption", value="initial AddRoundKey rk[10]; rounds 1..9 rk[9]..rk[1]; final round rk[0]",
         reason="Not written in the task text; follows FIPS 197 (inverse cipher) and the expected value of the TB vector.",
         check=dict(signal="round key select", rows="update rows 11..21 / no-update rows 1..11: keys 10,9,...,0")),
    dict(id="AA12", subject="key_done as an internal signal", value="key_done = 0 from reset and from the start edge of an update; 1 from the end of key step 10; stays 1 later",
         reason="The name and meaning are the architect's; the spec only requires 'expand first, then decrypt'. An RTL may encode this differently (for example a counter only).",
         check=dict(signal="key-expansion-done flag or its equivalent", rows="update row 11 first 1; no-update case 1 in all rows")),
    dict(id="AA13", subject="stored key form", value="all 11 round keys are kept; a no-update run does not re-expand",
         reason="Task text: 'the stored expanded key'. If the RTL stored only the cipher key and re-expanded each time, the no-update latency would be 22, not 12.",
         check=dict(signal="expanded key store", rows="no-update case: no key_cnt activity in rows 1..11")),
    dict(id="AA14", subject="byte order of i_key and i_data/o_data", value="byte 0 = most significant byte, row n%4, column n//4",
         reason="Fixed by the TB comment for i_data and by the TB vectors for the key and output (expected plaintext 3243f6a8... is the FIPS vector); listed so the RTL map can confirm it.",
         check=dict(signal="load of state_reg and of rk[0]", rows="row 1")),
]

ports_total, model["edges"] = ports_spec.apply(model["blocks"])
print("ports described", ports_total)
json.dump(model, open("model.json", "w"), indent=1)
assumptions += [
    dict(id="AA15", subject="internal control signals upd_load, start_accept, key_cnt, round_cnt", value="named and split as in model.json (upd_load = idle & i_start & i_update_key; start_accept = idle & i_start)",
         reason="Spec has no internal signals; an RTL may merge them in one FSM, use other encodings or one-hot state. The HDL map may mark a block as 'merged' if the function is the same.",
         check=dict(signal="FSM state / counters", rows="compare values per row with the schedule, not names")),
    dict(id="AA16", subject="add_round_key input mux", value="add_round_key.state comes from state_reg.q at round_cnt = 1 and from inv_sub_bytes.state_out at round_cnt = 2..11; the mux is counted with round_mux",
         reason="The initial AddRoundKey skips InvShiftRows/InvSubBytes. An RTL may instead apply those and bypass them with a mux, or add a separate initial XOR; the function per row is what counts.",
         check=dict(signal="input of the XOR with the round key", rows="first decrypt row: equals state_reg (ciphertext)")),
    dict(id="AA17", subject="round key store read for the key step", value="rk_prev = rk[key_cnt-1] is a combinational read of the registered store; the new key is written at the end of the same row",
         reason="Serial one-key-per-clock schedule (AA1). An RTL may keep only the last round key in a working register and the finished keys in the array.",
         check=dict(signal="round key register(s)", rows="update rows 1..10 each hold the next round key one row later")),
    dict(id="AA18", subject="latency numbers in ports_detail", value="combinational ports 0 cycles, registered ports 1 cycle; cumulative rows per case in schedule",
         reason="Consequence of AA1-AA4; any other register placement changes the numbers.",
         check=dict(signal="all ports", rows="per schedule")),
    dict(id="AA19", subject="model_cli argument encodings", value="rk_all = rk[0]||...||rk[10] (rk[0] most significant, 352 hex digits); counters as hex numbers; round_mux CLI only selects a path",
         reason="Needed for rtl blockcheck; the RTL array may use another index order, then the HDL engineer must map it (and say so).",
         check=dict(signal="expanded key array", rows="any row with key_done = 1")),
]
json.dump(assumptions, open("assumptions_arch.json", "w"), indent=1)
print("blocks", len(blocks), "assumptions", len(assumptions))
