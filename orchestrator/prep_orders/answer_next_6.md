Accepted: round_ff is the first to go wrong, and the record is in place.
On your doubt: before a start has been seen nothing may advance, so the counter holds its idle value; it leaves idle only on start. Decide the rest from the task text, not from the present code.

WORK ORDER 1.2
Goal:      Make round_ff hold idle until start is seen, and go through the rounds the task describes after it.
Look at:   only the always block that drives round_ff in aes128_decrypt.sv.
Keep:      the task requires decryption to wait for the key expansion when the key is updated. Whatever in this driver expresses that waiting stays; you are correcting the idle behaviour and the count, not removing conditions.
Use:       rtl show, rtl replace (this driver only), rtl sim, then the same rtl probe as before; when the sequence is as required: rtl mark round_ff fixed "kind=control golden=... observed=... source=...".
Done when: round_ff is recorded as fixed, or you have reverted and can say why it did not hold.
Report:    rtl next "found: ... / evidence: ... / unsure: ..."
