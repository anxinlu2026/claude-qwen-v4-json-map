# HDL agent.md additions (draft, general principles)

Insert after "Working rule (the file first)". The existing sections describe the work-order mode; this section describes the exchange mode.

## Exchange mode (rounds of files)

Applies when the architecture engineer and you exchange files in a shared folder instead of work orders.

1. **Alignment**: map each unit of the reference model to the unit of the implementation that does its work. Record facts and their evidence (file, line, quoted text, run output). When you cannot tell, write `unknown`; when several candidates fit, list them and name the main one. Do not copy values from the model into your record.
2. **Precondition of a comparison**: before you treat a comparison as evidence, check that the compared unit was exercised under valid operating conditions. A comparison made while the unit was not exercised is not evidence: say so, and state under what conditions the values were sampled.
3. **Unit-level verification**: verify a unit with the harness the architecture gave: feed the unit the inputs the implementation itself gave it, so a fault upstream does not hide a fault in this unit. Numbers produced by a tool are recorded by the tool; you do not edit them.
4. **Confidence and difficulty**: for each unit write a level and one sentence of reason. Low confidence is an honest result, not a failure.
5. **Questions and assumptions**: write what you are unsure of as a question (to the architecture) or as an assumption (falsifiable, with evidence). The architecture decides whether the model changes; you decide how the implementation changes.
6. **Traceable changes**: you may edit the implementation of your own unit when you judge it necessary. Each change is one record: a unique id, its basis (a message id or your own assumption), the place, before and after, the reason, and the verification after the change. After each change, rerun the unit-level verification and the whole-design regression. The count of changes comes from the difference to the original, not from memory.
7. **When blocked**: do not look for a way around a gate. Write what you compared, what you found, what you need, send it to the orchestrator and wait for the answer.
8. **Rounds**: each round you write a file for every unit (unchanged units say `no_change`). Replies to the architecture point at its message ids.
9. **Stopping**: when the whole-design test passes, stop changing and report.
