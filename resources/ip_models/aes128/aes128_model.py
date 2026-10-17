#!/usr/bin/env python3
"""Command-line front end for the AES-128 reference model in aes_ref_qwen.py (key expansion and decryption).

  python3 aes128_model.py roundkeys <key hex>
  python3 aes128_model.py decrypt <key hex> <ciphertext hex>
  python3 aes128_model.py block <name> <input hex> [<input hex> ...]     one block on the inputs you give

Blocks (each prints one hex value):
  inv_shift_rows STATE | inv_sub_bytes STATE | inv_mix_columns STATE | add_round_key STATE ROUNDKEY   (32 hex digits each)
  inv_mix_column COLUMN (8 hex digits: one column, row 0 first)
  next_round_key ROUNDKEY N   round key N (1..10) from round key N-1 (32 hex digits)
  rot_word WORD | sub_word WORD (8 hex digits) | xtime BYTE | gmul BYTE BYTE (2 hex digits)

All values are printed as 32 hex digits in block order: byte n of the block is state row n mod 4,
column n div 4 (the order used for the input/output block). The step order inside a decryption round
is the one the model uses: InvShiftRows, InvSubBytes, AddRoundKey, InvMixColumns.
"""
import sys
import aes_ref_qwen as m


def hx(state):
    return bytes(state[r][c] for c in range(4) for r in range(4)).hex()


def round_keys(key):
    w = m.key_expansion(key)
    return w, [[[w[4 * i + c][r] for c in range(4)] for r in range(4)] for i in range(11)]


def st_(b):
    return [[b[4 * c + r] for c in range(4)] for r in range(4)]


def block(name, v):
    """One block of the model on the given inputs (the same functions the validated decryption uses)."""
    if name == 'inv_shift_rows':
        return hx(m.inv_shift_rows(st_(v[0])))
    if name == 'inv_sub_bytes':
        return hx(m.inv_sub_bytes(st_(v[0])))
    if name == 'inv_mix_columns':
        return hx(m.inv_mix_columns(st_(v[0])))
    if name == 'add_round_key':
        return hx(m.inv_add_round_key(st_(v[0]), st_(v[1])))
    if name == 'inv_mix_column':
        s = m.inv_mix_columns([[v[0][r], 0, 0, 0] for r in range(4)])
        return bytes(s[r][0] for r in range(4)).hex()
    if name == 'next_round_key':
        n = int(v[1].hex())   # the round number is written in decimal: 1..10
        prev = [list(v[0][4 * i:4 * i + 4]) for i in range(4)]
        t = prev[3]; t = [m.SB[b] for b in (t[1], t[2], t[3], t[0])]; t[0] ^= m.RCON[n - 1]
        out = []
        for i in range(4):
            t = [prev[i][j] ^ t[j] for j in range(4)]; out.append(t)
        return bytes(b for w in out for b in w).hex()
    if name == 'rot_word':
        return bytes((v[0][1], v[0][2], v[0][3], v[0][0])).hex()
    if name == 'sub_word':
        return bytes(m.SB[b] for b in v[0]).hex()
    if name == 'xtime':
        return f'{m.xtime(v[0][0]):02x}'
    if name == 'gmul':
        return f'{m.gmul(v[0][0], v[1][0]):02x}'
    sys.exit('unknown block: ' + name)


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'roundkeys':
        w, rks = round_keys(bytes.fromhex(a[1]))
        for i in range(11):
            print(f'round key {i:2d} (words W[{4*i}..{4*i+3}]): {hx(rks[i])}')
    elif len(a) == 3 and a[0] == 'decrypt':
        key, ct = bytes.fromhex(a[1]), bytes.fromhex(a[2])
        w, rks = round_keys(key)
        s = [[ct[4 * c + r] for c in range(4)] for r in range(4)]
        print(f'input block                    : {hx(s)}')
        s = m.inv_add_round_key(s, rks[10]); print(f'after AddRoundKey(key 10)      : {hx(s)}')
        for n, k in enumerate(range(9, 0, -1), 1):
            s = m.inv_shift_rows(s);            print(f'round {n:2d} after InvShiftRows    : {hx(s)}')
            s = m.inv_sub_bytes(s);             print(f'round {n:2d} after InvSubBytes     : {hx(s)}')
            s = m.inv_add_round_key(s, rks[k]); print(f'round {n:2d} after AddRoundKey({k})  : {hx(s)}')
            s = m.inv_mix_columns(s);           print(f'round {n:2d} after InvMixColumns   : {hx(s)}')
        s = m.inv_shift_rows(s);            print(f'round 10 after InvShiftRows    : {hx(s)}')
        s = m.inv_sub_bytes(s);             print(f'round 10 after InvSubBytes     : {hx(s)}')
        s = m.inv_add_round_key(s, rks[0]); print(f'round 10 after AddRoundKey(0)  : {hx(s)}')
        print(f'output block (plaintext)       : {hx(s)}')
    elif len(a) >= 3 and a[0] == 'block':
        clean = [x.lower().replace('0x', '').replace('_', '') for x in a[2:]]
        print(block(a[1], [bytes.fromhex('0' * (len(x) % 2) + x) for x in clean]))
    else:
        print(__doc__); sys.exit(1)


if __name__ == '__main__':
    main()
