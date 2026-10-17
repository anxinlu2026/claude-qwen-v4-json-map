---
name: architecture-review
description: "Work orders of type ARCH-REVIEW: judge an HDL report against the meaning written beforehand, update the ledger, decide the next step."
version: 0.1.0-draft
---

# architecture-review — for work orders of type ARCH-REVIEW

One decision: what the evidence says, and what happens next.

1. **Is the comparison valid?** For each result: inputs and their source, instant, layout and conversion, the element compared.
   A result that is not shown comparable says nothing about the design or the model. Say which part is missing.
2. **Read it by the meaning you wrote beforehand.** Proven, struck out, or says nothing. A result that matches none of the cases
   is inconclusive: write what it excludes and what is still open.
3. **Check the evidence itself**: the run numbers exist, the values are in the raw output, shell results carry the command and the value.
4. **Update the ledger** (`rtl assumption set`): each affected assumption and fact, with its evidence. Fix what became inconsistent
   (an object and its status that say opposite things, two entries that cannot both stand). Retract a fact the new evidence contradicts.
5. **Decide the next step**: another ARCH-PLAN (the question changed), an HDL order that implements a change (state its location and
   intent), a confirm order, or "done". If the HDL engineer objected with evidence, answer the evidence.
6. **After two inconclusive reviews of the same question, go up a level**; do not write the same order again.

## The report (`review.md`, one page)

    validity: <per result: valid / not shown comparable - why>
    verdict: <assumption numbers: proven / struck out / inconclusive - by which result>
    ledger changes: <numbers and new status>
    next: <order type and its purpose, or done>
    unsure: <...>
