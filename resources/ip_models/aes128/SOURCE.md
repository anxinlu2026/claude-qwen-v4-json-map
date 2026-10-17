# Source

- `aes_ref_qwen.py`: written by the local model qwen3.8:27b-nvfp4 (Qwen Code agent) on 2026-10-09 during the
  run `runs/agentic-native-medium3-3-qwen-qc-hdl-debug-rtl3-20261009` (CVDP problem AES_encryption_decryption_0005),
  reconstructed from that run's log. It was written from the model's own knowledge of AES, not from the
  standard document, and corrected by the model in four steps until its result matched the testbench value
  and openssl. Accepted into the library by the user's decision on 2026-10-10 as the first AES entry.
  Only change made here: the self-test lines at the end of the file were placed under
  `if __name__ == "__main__":` so the file can be imported.
- `aes128_model.py`, `validate.py`: written by Claude on 2026-10-10. They call the functions of
  `aes_ref_qwen.py` and add no cipher logic of their own.
- Licence: project-internal, no third-party code.
- Standard the function is defined in: FIPS 197 (NIST). The code has not been checked clause by clause
  against that document.
