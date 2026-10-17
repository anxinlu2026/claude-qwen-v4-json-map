"""Command line access to the pure data-path blocks of model.py (for `rtl blockcheck --model`).
usage: python3 model_cli.py block <block_id> <hex arg1> [<hex arg2> ...]   -> output as lower-case hex on stdout
Hex arguments: no 0x needed; shorter than the port width is zero-padded on the left (numeric value).
Byte layout: byte 0 = most significant byte of the hex string (= bits [W-1:W-8] of the port).
Blocks (argument order -> output):
  load_block        i_data(32 hex)                                   -> state_in(32)
  output_map        q(32)                                            -> o_data(32)
  add_round_key     state(32) round_key(32)                          -> state_out(32)
  inv_shift_rows    state(32)                                        -> state_out(32)
  inv_sub_bytes     state(32)                                        -> state_out(32)
  inv_mix_columns   state(32)                                        -> state_out(32)
  round_key_select  rk_all(352: rk[0] first = most significant) round_cnt(1..11) -> round_key(32)
  round_mux         initial_path(32) round_path(32) final_path(32) round_cnt -> state_next(32)
  rot_word          w3(8)                                            -> rot(8)
  sub_word          rot(8)                                           -> sub(8)
  rcon_step         sub(8) n(1..10)                                  -> t(8)
  word_xor_chain    prev_round_key(32) t(8)                          -> next_round_key(32)
  key_expand_step   prev_round_key(32) n(1..10)                      -> next_round_key(32)
"""
import sys
import model as m

def val(x):
    return int(x.lower().replace("0x", "").replace("_", "") or "0", 16)

def blk(x, nbytes):
    return list(val(x).to_bytes(nbytes, "big"))

def hx(b):
    return bytes(b).hex()

def run(name, a):
    if name == "load_block":       return hx(m.load_block(val(a[0])))
    if name == "output_map":       return "%032x" % m.output_map(blk(a[0], 16))
    if name == "add_round_key":    return hx(m.add_round_key(blk(a[0], 16), blk(a[1], 16)))
    if name == "inv_shift_rows":   return hx(m.inv_shift_rows(blk(a[0], 16)))
    if name == "inv_sub_bytes":    return hx(m.inv_sub_bytes(blk(a[0], 16)))
    if name == "inv_mix_columns":  return hx(m.inv_mix_columns(blk(a[0], 16)))
    if name == "round_key_select":
        rk = blk(a[0], 176)
        return hx(rk[16 * m.round_key_index(val(a[1])):][:16])
    if name == "round_mux":
        r = val(a[3])
        return a_pick(a, 0 if r == 1 else (1 if r <= 10 else 2))
    if name == "rot_word":         return hx(m.rot_word(blk(a[0], 4)))
    if name == "sub_word":         return hx(m.sub_word(blk(a[0], 4)))
    if name == "rcon_step":        return hx(m.rcon_xor(blk(a[0], 4), val(a[1])))
    if name == "word_xor_chain":
        prev, t = blk(a[0], 16), blk(a[1], 4)
        out = []
        for j in range(4):
            t = [x ^ y for x, y in zip(prev[4 * j:4 * j + 4], t)]
            out += t
        return hx(out)
    if name == "key_expand_step":  return hx(m.next_round_key(blk(a[0], 16), val(a[1])))
    sys.exit("unknown block: " + name)

def a_pick(a, i):
    return hx(blk(a[i], 16))

if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "block":
        sys.exit(__doc__)
    print(run(sys.argv[2], sys.argv[3:]))
