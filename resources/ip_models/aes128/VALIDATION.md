# Validation

| Date | By | Independent source | What was compared | Result |
|---|---|---|---|---|
| 2026-10-09 | Qwen (during the run) | testbench value of AES_0005; openssl | decryption of 1 vector | match |
| 2026-10-10 | Claude | openssl (LibreSSL 3.3.6), `enc -d -aes-128-ecb -nopad` | decryption of 2 fixed vectors + 500 random key/ciphertext pairs | 502/502 |
| 2026-10-10 | Claude | openssl encrypt of the model's plaintext | round trip back to the ciphertext, same 502 pairs | 502/502 |
| 2026-10-10 | Claude | FIPS 197-upd1, Appendix A.1 (the text version in the standards folder) | expanded key words w[4]..w[43] for key 2b7e1516…4f3c | 40/40 agree |

Re-run: `python3 validate.py 500` (needs openssl).

Not validated: the per-step decryption states against an independent published source (the standard prints
a worked example for encryption only). The step order of the model matches Algorithm 3 of FIPS 197-upd1. Random keys exercising decryption end-to-end make an error in key expansion or in a
round step very unlikely, but this is indirect evidence.
