---
name: spec-planning
description: "A1.3 (architecture engineer): from the standard, list what an implementation must satisfy, with clause numbers and the worked examples it prints."
version: 0.1.0-draft
---

# spec-planning — what the standard requires

## Goal
A numbered list of the items the standard defines for the function of the task, and of the vectors it prints, so that test cases and the model can later be checked against the standard.

## Source
The standard in the standards folder, and the task text for the scope. Read it; do not recall it.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. From the task text, state the scope: which function, which parameters, which direction.
2. Find the clauses that define it. For each normative statement write one item: clause number, the statement in short, and its kind (function, step, ordering, table, constant, parameter, edge case, representation).
3. Collect every worked example or test vector the standard prints, with clause or page, inputs and expected outputs. Say which values are only end-to-end and which are intermediate.
4. List the variants and ambiguities the standard leaves (representation, byte order, naming), with the clause that states or omits them.
5. List what the standard does not give (for example intermediate values for a direction it does not work through).

## Output: `A1.3.md`
Sections, in this order: Scope (task text lines used) / Items (S1…: clause, statement, kind) / Vectors (V1…: clause, inputs, expected outputs, end-to-end or intermediate) / Variants and ambiguities / Not given by the standard.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every clause of the scope has an item or is named under "Not given by the standard"; every worked example found in the standard is a row in Vectors.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Only what the standard states. Quote clause numbers. No facts from memory.
- No statement about the RTL, the testbench or the model.
- A vector you cannot find in the text is not listed.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
