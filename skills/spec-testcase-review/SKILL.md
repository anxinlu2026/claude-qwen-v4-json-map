---
name: spec-testcase-review
description: "A1.5 (architecture engineer): for each item of the spec plan, say whether a test case of the testbench exercises it and compares the result."
version: 0.1.0-draft
---

# spec-testcase-review — which spec items have a test case

## Goal
A matrix of the spec plan against the test cases, so that it is known what a PASS or a FAIL of the testbench can and cannot say.

## Source
`A1.3.md` (items S#, vectors V#), `A1.1.md` (stimulus, checker, results), the testbench source.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. For each item S# and vector V#, find the test cases that exercise it: by the stimulus values or by the function the checker compares. Keep the testbench line.
2. Classify:
   - `covered`: the stimulus exercises the item and the checker compares a result that depends on it;
   - `partly`: exercised, but the result is not compared, or compared only in part (for example only the final output);
   - `not covered`: no test case;
   - `not verifiable here`: the item concerns internal values the testbench cannot see.
3. For each vector V#, say whether the testbench uses the same values or others.
4. List the test cases that map to no item, and the checks the testbench makes that the plan does not name.

## Output: `A1.5.md`
One table: item or vector / test case(s) and line / status / note (what is compared). Under it: the two lists of step 4.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every item S# and every vector V# of A1.3 has a row with a status; the two lists exist (write `none` if empty).
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Reading, and the results of A1.1 only. No coverage numbers: they belong to the verification unit. No judgement on the RTL.
- `covered` needs both the stimulus and a comparison; write what is compared.
- What rests on reading is labeled so.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
