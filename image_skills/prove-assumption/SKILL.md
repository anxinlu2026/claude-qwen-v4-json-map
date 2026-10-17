---
name: prove-assumption
description: "Finding the right explanation when several are possible: list them, find the observation that tells them apart, make it, strike out what it contradicts."
version: 1.1.0-container-draft
---

# prove-assumption

Use this whenever something is unexplained and more than one cause is possible.
An explanation is an assumption until an observation has separated it from the others.

1. **List the possible causes.** Two to four, written so that they exclude one another.
2. **For each one, say what you would see if it were true.** Look for an observation on which the causes give different results.
3. **Pick the cheapest observation that tells them apart.** Best is one that rules out half of them at once.
4. **Make that observation and strike out what it contradicts.** Repeat with what is left.
5. **What you read in the code is still an assumption.** It counts only when an observation or a simulation supports it.
6. **Change one thing at a time.** Otherwise you cannot tell which change produced the result.
7. **Prove a fix with the input that revealed the fault.** The same comparison, on that same input, must now come out right. If that input no longer occurs after the change, use another input that would also have shown the fault, and say why it would.

## How it looks when written down

    Unexplained:  <what was observed and what was expected>
    Causes:       A: ...        B: ...        C: ...
    If true:      A -> I would see ...    B -> I would see ...    C -> I would see ...
    Observation:  <the one check that gives a different result for A, B and C>
    Result:       <what was seen>   ->  struck out: ...   left: ...

## A small example

Unexplained: a lamp does not light when the switch is on.
Causes: A the bulb is broken; B the switch is broken; C there is no power at the socket.
If true: A -> another bulb lights in this lamp; B -> the lamp lights when the switch is bridged; C -> another device does not work at this socket either.
Observation: plug another device into the socket. It is the cheapest, and it separates C from A and B.
Result: the other device works -> struck out: C; left: A, B. Next observation: another bulb.

## In a report

When you are unsure, write it in this form under "unsure":
"possible: A ..., B ...; the observation that separates them: ...".
Then the next step is that observation, not more thinking.
