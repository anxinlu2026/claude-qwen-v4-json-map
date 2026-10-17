"""Check the model against openssl. Usage: python3 validate.py [number of random vectors, default 200]"""
import os, subprocess, sys
import aes_ref_qwen as m
import aes128_model as cli

def ossl(args, data, key):
    return subprocess.run(['openssl', 'enc', *args, '-aes-128-ecb', '-nopad', '-K', key.hex()], input=data, capture_output=True, check=True).stdout

n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
vecs = [(bytes.fromhex('2b7e151628aed2a6abf7158809cf4f3c'), bytes.fromhex('3925841d02dc09fbdc118597196a0b32')),
        (bytes.fromhex('000102030405060708090a0b0c0d0e0f'), bytes.fromhex('69c4e0d86a7b0430d8cdb78070b4c55a'))]
vecs += [(os.urandom(16), os.urandom(16)) for _ in range(n)]
# every function named decrypt* (the original one and any variant added in a local copy) is checked
funcs = [getattr(m, n) for n in dir(m) if n.startswith('decrypt') and callable(getattr(m, n))]
print('checking:', ', '.join(f.__name__ for f in funcs))
bad = 0
for f in funcs:
    for key, ct in vecs:
        out = f(ct, key)
        pt_ = out[0] if isinstance(out, tuple) else out
        bad += bytes(pt_) != ossl(['-d'], ct, key)
print(f'all decrypt* functions vs openssl -d : {len(funcs) * len(vecs) - bad}/{len(funcs) * len(vecs)}')
dec_ok = rk_ok = 0
for key, ct in vecs:
    pt, w = m.decrypt_block(ct, key)
    dec_ok += bytes(pt) == ossl(['-d'], ct, key)
    # round keys: decrypting with the model's own keys is not an independent check, so also confirm
    # that encrypt(openssl) of the model's plaintext returns the ciphertext
    rk_ok += ossl([], bytes(pt), key) == ct
print(f'decrypt vs openssl -d : {dec_ok}/{len(vecs)}')
print(f'openssl -e round trip : {rk_ok}/{len(vecs)}')
# block entry points: chained one after another they must reproduce the validated decryption
blk_ok = 0
for key, ct in vecs[:40]:
    w = m.key_expansion(key)
    rk = [bytes(b for c in range(4) for b in w[4 * i + c]).hex() for i in range(11)]
    chain = [key.hex()]
    for i in range(1, 11):
        chain.append(cli.block('next_round_key', [bytes.fromhex(chain[-1]), bytes.fromhex(f'{i:02d}')]))
    B = lambda n, *x: cli.block(n, [bytes.fromhex(y) for y in x])
    s_ = B('add_round_key', ct.hex(), rk[10])
    for k in range(9, 0, -1):
        s_ = B('inv_mix_columns', B('add_round_key', B('inv_sub_bytes', B('inv_shift_rows', s_)), rk[k]))
    s_ = B('add_round_key', B('inv_sub_bytes', B('inv_shift_rows', s_)), rk[0])
    blk_ok += (chain == rk) and bytes.fromhex(s_) == ossl(['-d'], ct, key)
print(f'block entry points chained vs openssl : {blk_ok}/{min(40, len(vecs))}')
ok = dec_ok == rk_ok == len(vecs) and bad == 0 and blk_ok == min(40, len(vecs))
print('HARNESS', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
