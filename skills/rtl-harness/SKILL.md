---
name: rtl-harness
description: "A1.1 (HDL engineer): run the testbench once on the untouched RTL and record what it drives, what it checks and what it returned."
version: 0.1.0-draft
---

# rtl-harness — run the testbench once and record the original baseline

## Goal
Give the team a recorded baseline: what the testbench does on the untouched RTL and what came out. You do not judge the design.

## Source
The RTL directory, the testbench directory, the simulator through `rtl sim`.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. List the files and the top module (names, paths, hashes).
2. Read the testbench. For each case write down: what is driven and when (stimulus), what is compared with what (checker), the expected values it holds, and the end condition. Keep the source line of each.
3. Run `rtl sim` once, unmodified. Keep the command, the working directory, the exit status, the time the simulation ended.
4. For each case: input values as the testbench gives them, expected, observed, verdict.
5. Note what the testbench does not check (outputs not compared, cases without expected values). This comes from reading: label it so.
6. Keep warnings and errors as they are; do not clean them.

## Output: `A1.1.md`
Sections, in this order: Run (command, directory, tool version, exit status, end time = the `$finish called at ...` line of the `rtl sim` output) / Files (path, hash = the `md5sum FILE` of every file listed) / Stimulus (per case: values, source line) / Checker (what is compared, source line) / Results (table: case, expected, observed, verdict) / Not checked (reading only) / Raw logs (paths).

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every case of the testbench has a row in Results with expected and observed, or `not_run: reason`; the simulation ran once and its run number is in Run.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Do not edit the RTL or the testbench. Do not diagnose. Do not run again to get another result.
- Reading and running are kept apart. What you could not run is `not_run`, with the reason.
- If the RTL fails, record the failure as it is; it is the baseline, not a defect to remove first.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
