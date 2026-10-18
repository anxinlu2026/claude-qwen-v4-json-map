---
name: unit-alignment
description: "Exchange mode (HDL engineer): align each unit of the reference model with the implementation, verify it with the unit-level harness, record confidence, difficulty, questions and assumptions in a file the architecture reads."
version: 0.1.0-draft
---

# unit-alignment — which implementation does the work of which model unit, and does it agree

## Goal
For each unit of the reference model, one record of: where the implementation does that work, what goes in and out, how the unit-level harness judged it, how sure you are, and what you could not settle.

## Source
The architecture's files for this round (model of the unit, harness of the unit, messages to you), the implementation, the whole-design test, the simulator and the tools the project provides. Use only commands the tool lists; if a skill or a note names a command the tool does not list, the tool is right.

## Method
1. Take the units in the order the architecture gave (inputs first).
2. Read the architecture's model of the unit. Find the statements of the implementation that do that work. Write the file, the lines and what the statements do (operation, direction, order, condition), copied from a numbered listing.
3. Find the signals that carry the unit's inputs and outputs. Record their width, kind, condition of validity, clock and edge, storage, latency. A value you cannot get from the implementation, the test or a run is `unknown`; do not take it from the model.
4. Before you rely on a comparison, check that the unit was exercised under valid conditions (see "Precondition"). Then run the unit-level harness. It feeds the unit the inputs the implementation gave it and compares the output with the reference; it also tells whether the implementation gave the inputs the architecture expected. A tool writes these numbers into your record.
5. Write confidence (high, medium, low) and difficulty (easy, medium, hard), each with one sentence of reason.
6. Write questions for the architecture and falsifiable assumptions with evidence. Do not state a cause as a fact.
7. Change the implementation only when you judge it necessary and your round allows it; record each change (see "Changes").
8. Validate the form of your files with the project's checker before you report.

## Precondition
A comparison is evidence only if the unit worked under valid conditions when its values were sampled. If it did not, write that the comparison is not evidence and under what conditions you sampled; find a way to create valid conditions without changing the test, and record how.

## Changes
Each change is one record with: unique id, basis (message id or your assumption), file and lines, before, after, reason, result of the unit-level harness after it, status (applied, proposed, reverted). After each change rerun the whole-design test. The number of changes comes from the difference to the original.

## Output
One file per unit and one for the whole design, with the envelope fields of the exchange (from, to, round, block), in the format the project defines. A unit that did not change says `no_change`.

## Do not
Change the test, the architecture's files or the tool's numbers. Look for a way around a gate: write what you compared, what you found and what you need, and wait for the answer.
