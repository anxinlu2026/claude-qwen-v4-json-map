# Standards index

| Function | Document | File | Publisher / source | Obtained | Parts useful for modelling |
|---|---|---|---|---|---|
| AES (128/192/256-bit keys): cipher, inverse cipher, key expansion | FIPS 197, update 1 (2023-05-09), 46 pages | `aes/NIST.FIPS.197-upd1.pdf`; text version for reading: `aes/NIST.FIPS.197-upd1.txt` (made with pdftotext -layout; figures are not included, check the PDF for them) | NIST, https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197-upd1.pdf (sha256 62c86eb5…7becd1) | 2026-10-10 | Algorithms 1-5: pseudocode for the cipher, key expansion and inverse cipher. Appendix A: key expansion examples for each key size, listing every word. Appendix B: step-by-step encryption example for key 2b7e1516…4f3c and input 3243f6a8…0734 (state after each step of each round). Appendix C: no values in the document; it refers to NIST's website for examples with intermediate values. |
