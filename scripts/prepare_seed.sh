#!/bin/bash
# git does not keep empty folders: recreate the empty folders of the seed (the problem has no docs/ files)
HERE="$(cd "$(dirname "$0")/.." && pwd)"
B="$HERE/seed_run/work/cvdp_agentic_AES_encryption_decryption/harness/5/before"
mkdir -p "$B/docs" "$B/rundir" "$B/rtl" "$B/verif"
