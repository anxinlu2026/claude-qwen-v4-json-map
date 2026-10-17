---
name: hdl-debug
description: "debug_fix tasks: work order by work order; golden values from a validated model; one driver, one edit, then confirm."
version: 8.2.0-container-draft
---

# hdl-debug — for tasks of type debug_fix

An existing RTL design gives wrong results and must be fixed. The testbench provided with the task
is the judge and is never modified. The fixed files in `/code/rtl` are the deliverable.

## Rule for every turn

Every turn carries out the current work order, and nothing else.
A work order names one goal, where to look, what to use, when it is done, and how to report.
When it is done: report with `rtl next "found: ... / evidence: ... / unsure: ..."` and wait.
The next work order comes from the orchestrator. Do not choose the next step yourself.
If you are unsure, or two instructions seem to conflict, do not deliberate: write it under
"unsure" in the report.

## Stages

Preparation, one work order each: read the task; read the testbench; run it once (`rtl sim`);
search `/opt/resources` and validate a model (`rtl model`); write the task sheet (`rtl sheetsubmit`).
Debugging: one conversation for one fault. Locate it, fix it, confirm it.
Closing: check the cases the testbench lacks; write the report.

## Core method

**1. A golden value is trusted only if it comes from a validated model; build only what you need.**
Search `/opt/resources` first (`INDEX.md`). If no model is there, model only the block being checked,
from the standard that defines it, and validate it against an independent source before use.

**2. Judge each block on the inputs it actually receives, and let the tool compare.**
`rtl blockcheck` feeds the probed inputs of a block to the model and compares the outputs.
Control signals are compared as a sequence (`rtl probe`, then `rtl mark ... "kind=control ..."`).

**3. One driver, one edit, then let the simulation give the verdict.**
Fix only the driver the work order names. An edit is an assumption to be proven, not a commitment:
apply it, then `rtl sim` and the same comparison again. However sure or unsure you feel, only that
verdict counts. Do not deliberate about whether it will work; if it does not hold, revert.
To prove a fix is correct, check it with the input that revealed the fault: the same comparison,
on that same input, must now come out right. If that input no longer occurs after the edit, use
another input that would also have shown the fault, and say why it would.

Commands: `/opt/skills/hdl-debug/references/rtl-tool.md`. Locating a fault: `/opt/skills/probe-signal/SKILL.md`.
