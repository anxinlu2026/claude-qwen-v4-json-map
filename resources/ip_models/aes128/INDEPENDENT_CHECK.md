# Independent AES value checks

When an AES value is needed, compute it — never take it from memory. The testbench
and a trusted tool are the sources of truth.

## AES-128 single block via openssl

```bash
# encrypt: plaintext -> ciphertext   (this image has no xxd: python3 converts hex <-> bytes)
python3 -c "import sys;sys.stdout.buffer.write(bytes.fromhex('<32 hex digits plaintext>'))" | \
  openssl enc -aes-128-ecb -nopad -K <32 hex digits key> | python3 -c "import sys;print(sys.stdin.buffer.read().hex())"

# decrypt: ciphertext -> plaintext
python3 -c "import sys;sys.stdout.buffer.write(bytes.fromhex('<32 hex digits ciphertext>'))" | \
  openssl enc -d -aes-128-ecb -nopad -K <32 hex digits key> | python3 -c "import sys;print(sys.stdin.buffer.read().hex())"
```

- `-nopad` for a single fixed 16-byte block; ECB uses no IV.
- Write the data to a file first if the shell quoting gets complicated.

## Known vectors (each row checked by running openssl on 2026-10-09)

| Commonly cited as | Key | Plaintext | Ciphertext |
|---|---|---|---|
| FIPS-197 Appendix B | `2b7e151628aed2a6abf7158809cf4f3c` | `3243f6a8885a308d313198a2e0370734` | `3925841d02dc09fbdc118597196a0b32` |
| FIPS-197 Appendix C.1 | `000102030405060708090a0b0c0d0e0f` | `00112233445566778899aabbccddeeff` | `69c4e0d86a7b0430d8cdb78070b4c55a` |
| a different NIST example | `2b7e151628aed2a6abf7158809cf4f3c` | `6bc1bee22e409f96e93d7e117393172a` | `3ad77bb40d7a3660a89ecaf32466ef97` |

Note: the plaintext `6bc1bee2…` does NOT pair with the ciphertext `3925841d…`. An
earlier version of this file paired them; that was a memory error. The key/plaintext/
ciphertext triples above were computed, but the document names in the first column
are from memory: confirm them in the publication if the name matters.

## Intermediate values (round keys, per-round state)

openssl gives only the final block. For intermediate values use a step-by-step
reference model written from the specification (FIPS-197, published by NIST) or
adapted from an established open-source implementation. **Validate it first:** its
end-to-end result must equal both the testbench vector and the openssl result for at
least two vectors (the table above). Only then compare its round keys / round states
with the RTL. Keep the validated model for reuse.

Things to settle explicitly when comparing with RTL:
- Byte order of the state: check whether the 4x4 state is filled column by column or
  row by row in the spec, in the RTL, and in the testbench comment, before calling a
  mismatch a bug.
- Which round key a given round uses; in decryption the keys are used in reverse order.

## Rule

Cite where each value came from (testbench line, openssl run, validated model). Label
any value you have not confirmed by execution as unconfirmed.
