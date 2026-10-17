---
name: find-assumption
description: "Work orders of type FIND ASSUMPTION: observe the symptom, then list at most two assumptions in the order to check them."
version: 1.0.0-container-draft
---

# find-assumption — for work orders of type FIND ASSUMPTION

An assumption is a possible cause. It rests on what was observed, not on reading alone.

1. **Observe the symptom first.** Probe or compare until you can say what is wrong, where, and from when
   (as many as you need within the time of the work order). What you observed goes into the report as it is.
   Compare with the validated model of the library (skill: use-ip-model; if the task sheet has a "model map"
   item, the pairing is there): `rtl blockcheck` on the block that gives the wrong result, with the inputs the
   design really has. `rtl sim` is open in this work order to confirm the state of the testbench; it is not an observation.
   An uncertainty that a comparison with the model can settle is settled by that comparison, not by thinking.
2. **Look at your record first** (`rtl assumption list`): the facts you measured are used, not measured again;
   what is proven or struck out is not proposed again; an open assumption may be the one to work on.
   A value or a rule you measured and will need again is recorded: `rtl assumption add --fact "FACT" "evidence"`. Record each new assumption you list:
   `rtl assumption add "OBJECT: the claim about which block / signal / behaviour"`.
2b. **List the possible causes: at most two**, written so that they exclude one another where they can.
   Leave out what the work order lists as proven or struck out.
3. **For each one, say what you would see if it were true**, and the one check that would show it.
4. **Put them in the order to check them:**
   first what lies upstream (a block cannot be judged while its inputs are wrong);
   then what is cheapest to check;
   then what rules out the most at once;
   "most likely" decides only between otherwise equal ones.
5. **What you read in the code is still an assumption.** Say which items rest on reading only.

## The list, as it goes into the report

    symptom: <what was observed, what was expected, run numbers>
    assumptions, in the order to check them:
      1. <cause> - if true I would see: ... - check: ... - why first: ...
      2. ...
    first observation: <the check of item 1>
