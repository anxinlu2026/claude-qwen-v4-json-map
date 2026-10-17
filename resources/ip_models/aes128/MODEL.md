# aes128 — AES-128 key expansion and decryption (step-by-step)

## What it models
- AES-128 key expansion: the 11 round keys (44 words) from a 128-bit key.
- AES-128 decryption of one 16-byte block, printing the state after every step of every round.
- Not included: encryption, AES-192/256, modes of operation.

## How to run
```bash
cd <this folder>
python3 aes128_model.py roundkeys <32 hex digits key>
python3 aes128_model.py decrypt   <32 hex digits key> <32 hex digits ciphertext>
```
One block on inputs you give (for `rtl blockcheck`): `python3 aes128_model.py block <name> <hex> ...`
(names and argument sizes: run `python3 aes128_model.py`).
From Python: `import aes_ref_qwen as m` then `m.key_expansion(key_bytes)` (list of 44 words, 4 bytes each)
and `m.decrypt_block(ct_bytes, key_bytes)` (returns plaintext bytes and the word list).

## Reading the output
- Every value is 32 hex digits in block order: byte n of the block is state row (n mod 4), column (n div 4).
  Check which order your RTL and its testbench use before comparing.
- Round key i consists of words W[4i]..W[4i+3]; decryption uses key 10 first and key 0 last.
- Step order inside a decryption round in this model: InvShiftRows, InvSubBytes, AddRoundKey, InvMixColumns
  (the last round has no InvMixColumns). An RTL design may register its state at a different point in the
  round; compare at matching points.

## Independent end-to-end check
See `INDEPENDENT_CHECK.md` (openssl commands for single-block AES-128 and three computed vectors).

## Harness, and changing the model locally
- Harness: `rtl model <this folder>` (runs `python3 validate.py`; compares against openssl; prints `HARNESS PASS` or `HARNESS FAIL`).
- If the model does not produce a value that corresponds to a signal of your RTL (another step order,
  another sampling point, a missing intermediate value): copy this folder to a writable place
  (for example `cp -r <this folder> /tmp/ip_work/`), change only what is needed there, and run the harness in
  the copy (`rtl model /tmp/ip_work/<name>`). A new routine that produces a final result must be named `decrypt...(ct, key)` and return the
  plaintext first, so that the harness checks it too. Use values from the changed model only after
  `HARNESS PASS`, and say in your report what you changed.

## Known limits
- End-to-end results are validated (see VALIDATION.md). All 40 expanded key words for the example key agree
  with the table in FIPS 197 Appendix A.1; the per-step decryption states have not been compared with a
  published source.
