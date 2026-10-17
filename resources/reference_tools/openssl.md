# openssl

Raw single-block AES as the standard defines it: ECB mode, no padding, key and data in hex.

    python3 -c "import sys;sys.stdout.buffer.write(bytes.fromhex('DATA_HEX'))" | openssl enc -aes-128-ecb -nopad -K KEY_HEX | od -An -tx1 | tr -d ' \n'      # encrypt
    python3 -c "import sys;sys.stdout.buffer.write(bytes.fromhex('DATA_HEX'))" | openssl enc -d -aes-128-ecb -nopad -K KEY_HEX | od -An -tx1 | tr -d ' \n'   # decrypt

Use `-aes-192-ecb` / `-aes-256-ecb` for the other key sizes. Output: the 16-byte result only; no
round keys, no round states.
