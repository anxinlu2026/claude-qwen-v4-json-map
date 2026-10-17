"""Sub-blocks of inv_mix_columns, from the algebra of FIPS 197 (eq. 5.10), for the drill-down. Same conventions as model_cli.py.
usage: python3 model_cli_sub.py block <id> <hex args>
  gmul_state   state(32 hex) k(hex)                      -> every byte multiplied by k in GF(2^8) (poly 0x11B), 32 hex
  mix_combine  p0e(32) p0b(32) p0d(32) p09(32)           -> per column: out_r = p0e[r] ^ p0b[r+1] ^ p0d[r+2] ^ p09[r+3] (index mod 4), 32 hex
  (products p_k = gmul_state(state, k); inv_mix_columns(state) = mix_combine(p0e, p0b, p0d, p09))"""
import sys
import model as m

def val(x): return int(x.lower().replace("0x", "").replace("_", "").replace("=", "") or "0", 16)
def blk(x): return list(val(x).to_bytes(16, "big"))

def gmul_state(state, k): return [m.gmul(b, k) for b in state]
def mix_combine(p0e, p0b, p0d, p09):
    out = [0] * 16
    for c in range(4):
        for r in range(4):
            out[4 * c + r] = p0e[4 * c + r] ^ p0b[4 * c + (r + 1) % 4] ^ p0d[4 * c + (r + 2) % 4] ^ p09[4 * c + (r + 3) % 4]
    return out

if __name__ == "__main__":
    a = sys.argv
    if len(a) < 3 or a[1] != "block":
        sys.exit(__doc__)
    if a[2] == "gmul_state":
        print(bytes(gmul_state(blk(a[3]), val(a[4]))).hex())
    elif a[2] == "mix_combine":
        print(bytes(mix_combine(*[blk(x) for x in a[3:7]])).hex())
    else:
        sys.exit(__doc__)
