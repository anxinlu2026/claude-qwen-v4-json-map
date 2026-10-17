[work order report, request 1]

State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; no testbench run yet; task sheet not approved; model not validated

## Report
found: aes128_decrypt must take 128-bit ciphertext i_data + 128-bit key i_key, expand the key into 11 round keys (44 words) via aes128_key_expansion when (i_update_key & i_start & o_done), then run AES-128 decryption = 1 initial AddRoundKey + 9 rounds of InvShiftRows/InvSubBytes/AddRoundKey/InvMixColumns + 1 final round (InvShiftRows/InvSubBytes/AddRoundKey, no InvMixColumns), producing 128-bit plaintext on o_data when o_done. FIPS-197 vector: key 2b7e151628aed2a6abf7158809cf4f3c, ciphertext 3925841d02dc09fbdc118597196a0b32 -> plaintext 3243f6a8885a308d313198a2e0370734. LIMITS (must NOT change): the aes128_decrypt port interface; the sbox, inv_sbox modules and Rcon values (stated already tested/correct). Internal block interfaces may be changed. / evidence: task text + rtl/aes128_decrypt.sv, rtl/aes128_key_expansion.sv, rtl/sbox.sv, rtl/inv_sbox.sv, verif/tb_aes128_dec.sv / unsure: which specific internal line(s) are buggy (to be found in the debug work order), and whether the key-expansion timing/round sequencing in aes128_decrypt.sv is part of the bug.

## Recorded comparisons
(none)

## Rule-based suggestion of the tool (for reference, not shown to the agent)
NEXT: rtl sim   (run the testbench once on the untouched design and note what fails)

## Last commands and their output

