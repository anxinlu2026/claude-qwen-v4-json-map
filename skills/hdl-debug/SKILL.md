---
name: hdl-debug
description: "debug_fix tasks: overview of how the work is organised (work orders by type)."
version: 9.0.0-container-draft
---

# hdl-debug — overview for tasks of type debug_fix

An existing RTL design gives wrong results and must be fixed. The testbench provided with the task
is the judge and is never modified. The fixed files in `/code/rtl` are the deliverable.

The work is done by work orders from the orchestrator. Each work order has a type; the type fixes which
skill applies (its text comes with the order) and which `rtl` commands are available:

| Type | What happens in it | Skill |
|---|---|---|
| TASK LIST | read the task and the testbench, run it once, validate a model, write the task sheet | task-sheet |
| FIND ASSUMPTION | observe the symptom, list at most two possible causes in the order to check them | find-assumption |
| PROVE ASSUMPTION | check them one by one with the tools: proven, or struck out | prove-assumption |
| FIX | one edit to one driver | fix-one-driver |
| CONFIRM FIX | the comparison that showed the fault, on the input that showed it | confirm-fix |
| CLOSING | the cases the testbench lacks; the report | closing |

Two things hold in every type:
- A golden value is trusted only if it comes from a validated model (`/opt/resources`; `rtl model`).
  How a model is used on a block of the design: skill `use-ip-model` (it comes with FIND, PROVE and CONFIRM FIX orders).
- When you cannot settle something yourself, you ask (skill: uncertainty).

Commands: `/opt/skills/hdl-debug/references/rtl-tool.md`.
