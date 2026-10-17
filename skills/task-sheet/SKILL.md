---
name: task-sheet
description: "Work orders of type TASK LIST: the five preparation steps and the task sheet."
version: 1.0.0-container-draft
---

# task-sheet — for work orders of type TASK LIST

Five steps, one work order each, in this order: read the task; read the testbench; run it once
(`rtl sim`) and note what fails; search `/opt/resources` (INDEX.md) and validate a model of the
function if one is there (`rtl model DIR`; read its MODEL.md, BLOCKS.txt and VALIDATION.md and note what has an
independent source and what has not); write the task sheet and submit it (`rtl sheetsubmit`).

## Task type: the first "yes" decides
a. The task says an existing design gives wrong results and must be fixed -> debug_fix.
b. The module to deliver works already and the task asks to change what it does -> feature_modification.
c. The deliverable is a new module that mainly instantiates and connects given modules -> module_integration.
d. The module to deliver has no implementation yet -> spec_to_rtl.
Judge by the module you must deliver, not by whether the rtl folder holds files. If none fits: "other", and why.

## Task sheet: /tmp/task_sheet.md, each item under its own heading, filled in from what you read and saw
task type (and the question that decided it) / goal / files to create or modify / what must not be changed /
available resources / golden source (what /opt/resources holds for this function, or what would have to be built) /
model map (for each block you expect to judge: design block <- its inputs | block of the validated model | instant its
inputs are complete | byte/bit layout; where the model has no such block or the step order differs, say so; skill: use-ip-model) /
facts stated in the task that narrow the work / observed failure (what rtl sim showed) /
testbench trust (can its expected values be trusted, and why) / testbench coverage (what it exercises, and which
cases of the task it does not) / how you will check the result.
