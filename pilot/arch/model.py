"""AES-128 decryption IP: block functions and a cycle-level top model (architecture step A).

Data layout everywhere: a 128-bit value is a list of 16 bytes, byte n = bits [127-8n : 120-8n]
(byte 0 = most significant byte of the port), state row = n % 4, column = n // 4 (FIPS 197).
A 32-bit word is a list of 4 bytes (byte 0 = most significant).  Round key i = W[4i]..W[4i+3];
word j of a round key is column j (bytes 4j..4j+3).
"""

# ---------------------------------------------------------------- GF(2^8), tables built from algebra
def xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a

def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = xtime(a)
        b >>= 1
    return r

def _build_sbox():
    sb = []
    for x in range(256):
        inv = 0
        if x:
            inv = next(y for y in range(1, 256) if gmul(x, y) == 1)
        s = inv
        for k in range(1, 5):
            s ^= ((inv << k) | (inv >> (8 - k))) & 0xFF
        sb.append(s ^ 0x63)
    return sb

SBOX = _build_sbox()
INV_SBOX = [0] * 256
for _i, _v in enumerate(SBOX):
    INV_SBOX[_v] = _i
RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]   # Rcon[1..10]

# ---------------------------------------------------------------- conversions
def to_bytes(x):            # 128-bit int -> 16 bytes, byte 0 = MSB
    return list(x.to_bytes(16, "big"))

def to_int(b):
    return int.from_bytes(bytes(b), "big")

# ---------------------------------------------------------------- data path blocks (all on 16-byte lists)
def load_block(i_data):
    """Load of the input block: port i_data (128 bit int) -> state bytes (byte n = row n%4, col n//4)."""
    return to_bytes(i_data)

def add_round_key(state, round_key):
    return [s ^ k for s, k in zip(state, round_key)]

def inv_shift_rows(state):
    """Row r rotated right by r columns: out[row r, col c] = in[row r, col (c - r) mod 4]."""
    out = [0] * 16
    for r in range(4):
        for c in range(4):
            out[4 * c + r] = state[4 * ((c - r) % 4) + r]
    return out

def inv_sub_bytes(state):
    return [INV_SBOX[b] for b in state]

def inv_mix_columns(state):
    M = [[14, 11, 13, 9], [9, 14, 11, 13], [13, 9, 14, 11], [11, 13, 9, 14]]
    out = [0] * 16
    for c in range(4):
        col = state[4 * c:4 * c + 4]
        for r in range(4):
            v = 0
            for k in range(4):
                v ^= gmul(M[r][k], col[k])
            out[4 * c + r] = v
    return out

def output_map(state):
    """Output mapping: state bytes -> port o_data (128 bit int), inverse of load_block."""
    return to_int(state)

# ---------------------------------------------------------------- key expansion blocks
def rot_word(w):
    return [w[1], w[2], w[3], w[0]]

def sub_word(w):
    return [SBOX[b] for b in w]

def rcon_xor(w, n):
    """XOR Rcon[n] (n = 1..10) into the most significant byte (byte 0) of the word."""
    return [w[0] ^ RCON[n - 1]] + list(w[1:])

def next_round_key(prev, n):
    """One key-expansion step: round key n-1 -> round key n (n = 1..10).
    w0 = prev.w0 ^ Rcon(SubWord(RotWord(prev.w3))); w1 = prev.w1 ^ w0; w2 = prev.w2 ^ w1; w3 = prev.w3 ^ w2."""
    t = rcon_xor(sub_word(rot_word(prev[12:16])), n)
    out = []
    for j in range(4):
        t = [a ^ b for a, b in zip(prev[4 * j:4 * j + 4], t)]
        out += t
    return out

def key_expansion(key16):
    rks = [list(key16)]
    for n in range(1, 11):
        rks.append(next_round_key(rks[-1], n))
    return rks

# ---------------------------------------------------------------- whole-block decrypt (functional reference)
def decrypt_block(ct_int, key_int):
    rks = key_expansion(to_bytes(key_int))
    s = add_round_key(load_block(ct_int), rks[10])
    for k in range(9, 0, -1):
        s = inv_mix_columns(add_round_key(inv_sub_bytes(inv_shift_rows(s)), rks[k]))
    s = add_round_key(inv_sub_bytes(inv_shift_rows(s)), rks[0])
    return output_map(s)

# ---------------------------------------------------------------- control blocks and round selection
def round_key_index(r):
    """round_key_select: round_cnt r (1..11) -> index of the round key: 1 -> 10, r = 2..11 -> 11 - r (9..0)."""
    return 10 if r == 1 else 11 - r

def round_step(state, rk, r):
    """round_mux + data path for round_cnt r (1..11): the new state_reg value."""
    k = rk[round_key_index(r)]
    if r == 1:
        return add_round_key(state, k)
    s = add_round_key(inv_sub_bytes(inv_shift_rows(state)), k)
    return inv_mix_columns(s) if r <= 10 else s

def next_key_cnt(key_cnt, round_cnt, i_start, i_update_key):
    """key_counter: next value. 0 -> 1 on an accepted start with update (idle); n -> n+1; 10 -> 0."""
    if key_cnt:
        return 0 if key_cnt == 10 else key_cnt + 1
    return 1 if (round_cnt == 0 and i_start and i_update_key) else 0

def next_round_cnt(key_cnt, round_cnt, i_start, i_update_key):
    """round_counter: next value. idle & start & !update -> 1; key_cnt == 10 -> 1; r -> r+1; 11 -> 0."""
    if key_cnt:
        return 1 if key_cnt == 10 else 0
    if round_cnt:
        return 0 if round_cnt == 11 else round_cnt + 1
    return 1 if (i_start and not i_update_key) else 0

def next_done(round_cnt):
    """done_gen: o_done next value = 1 exactly when round_cnt == 11."""
    return int(round_cnt == 11)

def next_key_done(key_done, key_cnt, upd_load):
    """key_done_flag: 0 on an accepted start with update, 1 after key step 10, else unchanged."""
    if upd_load:
        return 0
    return 1 if key_cnt == 10 else key_done

# ---------------------------------------------------------------- cycle-level top model
class Top:
    """Registers: state, rk[0..10], key_cnt (0 or 1..10), round_cnt (0 idle, 1..11), key_done, upd(unused: the
    start edge acts at once), done.  One call to step() = one rising clock edge.
    Inputs are those present just before the edge; the returned dict is the register view AFTER the edge
    (= the values seen in the next row).  view() gives the values seen BEFORE the next edge."""
    def __init__(self):
        self.reset()

    def reset(self):                                   # asynchronous reset, active low (AA reset values)
        self.state = [0] * 16
        self.rk = [[0] * 16 for _ in range(11)]
        self.key_cnt = 0
        self.round_cnt = 0
        self.key_done = 0
        self.done = 0

    @property
    def busy(self):
        return self.key_cnt != 0 or self.round_cnt != 0

    def view(self):
        return {"key_cnt": self.key_cnt, "round": self.round_cnt, "key_done": self.key_done,
                "o_done": self.done, "o_data": output_map(self.state)}

    def step(self, i_start=0, i_update_key=0, i_key=0, i_data=0):
        kc, rc = self.key_cnt, self.round_cnt
        idle = kc == 0 and rc == 0
        upd_load = int(idle and i_start and i_update_key)       # key_counter output
        start_accept = int(idle and i_start)                    # round_counter output
        # next values of all registers are computed from the current ones, then applied together
        n_kc = next_key_cnt(kc, rc, i_start, i_update_key)
        n_rc = next_round_cnt(kc, rc, i_start, i_update_key)
        n_done = next_done(rc)
        n_kd = next_key_done(self.key_done, kc, upd_load)
        if upd_load:
            self.rk[0] = to_bytes(i_key)
        if kc:
            self.rk[kc] = next_round_key(self.rk[kc - 1], kc)
        if start_accept:
            self.state = load_block(i_data)
        elif rc:
            self.state = round_step(self.state, self.rk, rc)
        self.key_cnt, self.round_cnt, self.done, self.key_done = n_kc, n_rc, n_done, n_kd
        return self.view()

def run_case(update, key, data, prior_key=None, idle_rows=2, max_rows=100):
    """Drive one operation like the testbench: i_start for one row, then 0.  Returns (rows, o_data).
    rows[t] = values seen during row t (row 0 = start row, registers before the start edge)."""
    t = Top()
    t.reset()
    if not update:                                      # stored key: do an earlier update run first
        t.key_done = 0
        t.rk = key_expansion(to_bytes(prior_key if prior_key is not None else key))
        t.key_done = 1
    rows = [dict(t.view(), i_start=1, i_update_key=int(update))]
    t.step(1, int(update), key, data)
    while True:
        v = t.view()
        rows.append(dict(v, i_start=0, i_update_key=0))
        if v["o_done"] or len(rows) > max_rows:
            return rows, v["o_data"]
        t.step(0, 0, 0, 0)
