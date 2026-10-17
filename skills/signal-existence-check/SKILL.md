---
name: signal-existence-check
description: "A2.5 (HDL engineer): for the paired signals, check that each can be read in the simulation and write its full name."
version: 0.1.0-draft
---

# signal-existence-check — can the signal be read

## Goal
For each signal of the signal pairing, say whether the tools can read it in the simulation, its full hierarchical name as the tool accepts it, and one sampled value. You do not compare and you do not judge.

## Source
The signal pairing delivery, the testbench, the simulator through `rtl probe`.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Record the version (hash) of the signal pairing delivery.
2. Put all signals into as few `rtl probe` runs as the tool allows (a run counts once, however many signals it reads). Keep each command and the run number.
3. For each signal: readable or not, the full name as the tool printed it, one value at one instant (say which instant).
4. A signal that cannot be read is recorded as it is, with the tool's message; do not rename it to make it work.
5. Signals inside generate blocks need the full path; try the path the source gives and record what the tool answers.

## Output: `A2.5.md`
Sections, in this order: Run (commands, run numbers, instants) / Signals (signal, readable or not, full name, one value, instant) / Not readable (signal, tool message) / Raw logs (paths).

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every signal of the signal pairing has a row in Signals or in Not readable; every run number is in Run.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Existence and readability only: no match or mismatch, no verdict on the design.
- Do not edit the RTL or the testbench.
- Values are copied from the tool output character for character.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
