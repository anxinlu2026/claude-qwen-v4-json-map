# IP model index

| Name | Function | Standard | Language | Intermediate values | Status | Entry |
|---|---|---|---|---|---|---|
| aes128 | AES-128 key expansion and single-block decryption | FIPS 197 | Python 3 | 11 round keys; state after every step of every decryption round | validated end-to-end (502 vectors vs openssl); all 40 expanded key words agree with FIPS 197 App. A.1; decryption states not independently checked | `aes128/MODEL.md` |
