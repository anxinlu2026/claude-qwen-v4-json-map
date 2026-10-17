---
name: probe-signal
description: "Locate a faulty circuit by comparing probed RTL signals with golden values, top-down, and fix only that circuit."
version: 1.3.0-container-draft
---

# probe-signal

Use `rtl probe` to compare the inputs and outputs of RTL code with golden values, top-down, breaking
the design into smaller blocks until the faulty circuit is located; then reason out the fix for
that circuit.

1. **Compare.** Check a block with `rtl blockcheck`: its probed inputs go into the validated model
   of that block and the outputs are compared. Mismatch: go inside that block. Match: the block is
   correct for what it receives; go one block back toward the inputs.
2. **Where it ends.** Every signal is driven by one `always` block or one combinational assignment.
   When the inputs of that driver match golden and its output does not, that driver is the faulty
   circuit.
3. **Fix only that driver.** `rtl replace`, `rtl sim`, then repeat the same comparison. Output now
   matches golden and the run is not worse: keep the fix, even if the testbench still fails.
   Otherwise `rtl revert` and go back one level: compare the stage upstream again.
4. **Ask when the method does not get there.** No mismatch found down to single drivers, no golden
   value for a signal, two fixes of the same driver that were reverted, or the fault turns out to be
   logic that does not exist in the RTL and would have to be added: `rtl ask "..."` and wait for
   the orchestrator's instructions. The `rtl` command enforces this: at these points it refuses to go on
   until you have asked.

For debug_fix tasks, rewriting a module, redesigning a block, or changing code that no comparison has
shown to be faulty needs the orchestrator's permission first (`rtl ask`); doing it without permission
ends the task.

Commands: `/opt/skills/hdl-debug/references/rtl-tool.md`.
