---
name: confirm-fix
description: "Work orders of type CONFIRM FIX: prove the fix with the input that revealed the fault."
version: 1.0.0-container-draft
---

# confirm-fix — for work orders of type CONFIRM FIX

1. **Repeat the comparison that showed the fault, on the input that showed it.** `rtl history WORD` gives
   the command. The same comparison, on that same input, must now come out right.
2. **If that input no longer occurs after the edit**, use another input that would also have shown the
   fault, and say why it would. A match on an input that could not have shown the fault is not a confirmation.
3. **Decide:** recorded as fixed -> report. Not fixed -> `rtl revert`, and report what the comparison showed.
   An edit that is not confirmed is not kept, even if it may be right.
