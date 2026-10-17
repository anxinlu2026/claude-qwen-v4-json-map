---
name: prove-assumption
description: "Work orders of type PROVE ASSUMPTION: check the listed assumptions one by one with the tools and decide each: proven or struck out."
version: 2.0.0-container-draft
---

# prove-assumption — for work orders of type PROVE ASSUMPTION

The reasoning in this kind of work order is about one thing only: how to use the tools to show whether
an assumption is true.

1. **Take the assumptions in the order given**, one at a time (the number of observations is not limited; the time of the work order is).
2. **Make the check of that assumption, then decide before going on:** proven, or struck out. Record the
   decision at once, with its evidence (a measured fact that later work needs: `rtl assumption add --fact`): `rtl assumption set A3 proven|struck-out|open "tool run numbers and result lines"`.
   A block is judged on the inputs it actually receives: `rtl blockcheck` feeds the probed inputs to the
   validated model and compares the outputs. A control signal is judged as a sequence (`rtl probe`, then
   `rtl mark SIGNAL ... "kind=control ..."`). A value held in several signals is joined with `+`.
3. **Look at the inputs of a comparison before you trust it.** A match on inputs that could not have shown
   the fault proves nothing; say why your inputs could.
4. **Stop at the first assumption that is proven** and report, unless the work order says to check them all.
   Two assumptions can be true at once: one proven does not strike out the others.
5. **A mismatch in a block of several drivers:** the next list of assumptions is about its parts; break it
   down until one driver is left.

## The result, as it goes into the report

    proven:      <which assumptions> - by: run numbers and result lines
    struck out:  <which> - by: ...
    still open:  <which were not checked>
