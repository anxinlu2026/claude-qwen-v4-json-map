[sheet submitted for review, submission 1]

# Task sheet — AES-128 decryption RTL debug

## Goal
Fix the AES-128 decryption RTL so that `rtl sim` reports PASS on both testbench cases,
i.e. `o_data == 128'h3243f6a8885a308d313198a2e0370734` for the FIPS-197 vector
(ciphertext 3925841d02dc09fbdc118597196a0b32, key 2b7e151628aed2a6abf7158809cf4f3c).
Task type: **debug_fix** — an existing RTL gives wrong results and must be fixed; the
testbench is the judge and is never modified; the fixed files in /code/rtl are the deliverable.
Deciding question: the design already exists and produces the wrong result (rtl sim run #1 =
FAIL on both cases), so the job is to locate and fix the fault, not to design from scratch.

## Files to change
- rtl/aes128_decrypt.sv — allowed (the deliverable; internal logic may be fixed).
- rtl/aes128_key_expansion.sv — allowed if the fault is there.
- rtl/sbox.sv, rtl/inv_sbox.sv — MUST NOT change (stated already tested/correct).
- verif/tb_aes128_dec.sv — MUST NOT change (the judge).
- The `aes128_decrypt` port interface MUST NOT change; internal block interfaces may.

## Facts
- Top module aes128_decrypt: 128-bit key + 128-bit ciphertext in, 128-bit plaintext out,
  async reset, o_done flag. Internal blocks: aes128_key_expansion, sbox, inv_sbox.
- Decryption = 1 initial AddRoundKey + 9 rounds of InvShiftRows/InvSubBytes/AddRoundKey/
  InvMixColumns + final round (InvShiftRows/InvSubBytes/AddRoundKey, no InvMixColumns).
- Key expansion = 11 round keys / 44 words W[0..43] from the 128-bit key.
- Golden source (validated, on record): /opt/resources/ip_models/aes128 (FIPS 197, Python).
  `rtl model` = HARNESS PASS (decrypt vs openssl 202/202, round-trip 202/202, block entry
  points 40/40, 40 key words agree with FIPS 197 App A.1). Gives roundkeys, full decrypt
  (state after every step of every round), and per-block ops (add_round_key, inv_shift_rows,
  inv_sub_bytes, inv_mix_columns, inv_mix_column, next_round_key, rot_word, sub_word, xtime,
  gmul). Byte order: byte n = row (n mod 4), column (n div 4) — confirm it matches the RTL
  state layout before comparing intermediates.
- sbox, inv_sbox and the Rcon values are stated already tested and correct; do not touch them.

## Observed failure
rtl sim run #1 (untouched design): 2 FAIL, 0 PASS.
- Case 1 Simple_test(1'b1) (update_key=1, expand key + decrypt):
  expected 3243f6a8885a308d313198a2e0370734, observed 00000000000000600000000000000000.
- Case 2 Simple_test(1'b0) (update_key=0, reuse stored key, only i_start):
  expected 3243f6a8885a308d313198a2e0370734, observed 00000000000000970000000000000000.
Both outputs are all-zero except one byte — the decryption pipeline / round sequencing is broken.

## Testbench trust
The testbench (verif/tb_aes128_dec.sv) is the judge and is never modified. It drives the
FIPS-197 key/ciphertext, samples o_data after posedge o_done, and checks against the known
plaintext 3243f6a8885a308d313198a2e0370734. Its expected value is the FIPS-197 plaintext and
is trusted; the golden aes128 model (HARNESS PASS vs openssl) independently confirms it.

## Testbench coverage
Covers: (1) update_key=1 (full key expansion + decryption); (2) update_key=0 (reuse stored
expanded key, only i_start) — both on the single FIPS-197 vector, both expecting the same
plaintext.
Does NOT cover: a direct check of the expanded key / 44 words / 11 round keys (o_expanded_key);
an isolated test of key expansion (RotWord/SubWord/Rcon/XOR W[i-4]); an isolated test of the
InvMixColumns / InvShiftRows / InvSubBytes stages; a separate case for the final round
(round 10, no InvMixColumns); any key/ciphertext other than the single FIPS-197 vector; and an
explicit check of o_done / key_done timing or the serial key-expansion-before-decryption
ordering (only the end result). These gaps are to be checked at closing.

## Method (one fault per conversation: locate, one edit, confirm)
1. Probe the RTL round-by-round and compare each stage's output against the aes128 model
   (rtl blockcheck / rtl mark), starting from the stage that first diverges.
2. Apply one edit (rtl replace) to the driver the comparison names.
3. Confirm with rtl sim (must reach PASS on both cases) and re-run the same blockcheck on the
   input that revealed the fault.
4. If an edit does not hold, revert (rtl revert) and compare one level upstream.

## Acceptance
rtl sim reports PASS on both Simple_test cases (o_data == 3243f6a8885a308d313198a2e0370734),
with the fix confirmed by the same blockcheck on the input that revealed the fault.
