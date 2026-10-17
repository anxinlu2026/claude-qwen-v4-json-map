---
name: fix-one-driver
description: "Work orders of type FIX: one edit to one driver."
version: 1.0.0-container-draft
---

# fix-one-driver — for work orders of type FIX

1. **Look at the driver the work order names** (`rtl show`), and nothing else.
2. **Make one contiguous edit** (`rtl replace`). A declaration may sit directly above the block that uses it.
   Change one thing at a time: otherwise you cannot tell which change produced the result.
3. **Run `rtl sim`** and report what it says now. Confirming the fix is the next work order.

An edit is an assumption to be proven, not a commitment. However sure or unsure you feel, only the
simulation and the comparison give the verdict. Do not deliberate about whether it will work: apply it.
Rewriting a module or redesigning a block is not a fix of one driver; it needs the orchestrator's
permission (`rtl ask`).
