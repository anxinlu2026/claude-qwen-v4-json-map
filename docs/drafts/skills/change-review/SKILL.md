---
name: change-review
description: "Exchange mode (architecture engineer): review the changes the HDL engineer made, classify each against the specification and the tests, reconcile the counts, decide whether the work can be closed."
version: 0.1.0-draft
---

# change-review — are the changes justified, and is the record complete

## Goal
A judgement per change with its basis, a reconciliation of the recorded changes with the actual difference, the list of what remains doubtful, and whether the work can be closed.

## Source
The HDL engineer's files, the tool files, the difference between the original and the final implementation, the specification, the standard and the tests. Numbers come from the tool files; a statement of the HDL engineer that disagrees with a tool file is pointed out, not adopted.

## Method
1. Match every recorded change to a hunk of the difference, and every hunk to a record. List what does not match on either side. Count how many distinct places changed and how many records repeat one change.
2. Classify each change: required by the specification or a test; an equivalent rewrite; an exception for a particular value or situation. Write the basis (section, line of the test, evidence of the HDL engineer).
3. Look for constants or special cases that exist only to pass the test data. A passing test is not enough: say what else supports the change.
4. Check that no change was made to the reference model to fit the implementation, and that each refusal or acceptance of a model change has its basis.
5. For each unit the HDL engineer marked aligned, say whether the evidence supports it, and of what kind (direct, indirect, only reading).
6. List what remains doubtful and what it would cost, separating what blocks closing from what only strengthens.
7. State whether the work can be closed and why. Do not write an unverified assumption as a conclusion.

## Output
Per change: classification, basis. Reconciliation of counts. Doubts and risks. Closing judgement. Observations on the process, including confounding factors for any claim that the process helped.
