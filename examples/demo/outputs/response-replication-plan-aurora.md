# Recommended approach

Days 1–3 freeze the code commit, datasets, board firmware, clocks, power modes, and timing definition; rebuild environments before measuring. Days 4–6 run smoke tests and log every failure. Days 7–10 randomize model and board order, warm-up policy, and repeated timing blocks while preserving raw traces. Days 11–12 analyze per-board distributions and sensitivity to setup choices. Reserve two days for reruns. Accept the claim only if the predeclared latency statistic and interval meet the stated tolerance on both boards.

It uses a compact decision tree and explicit stop conditions. The main limitation is that each branch needs repeated measurements before attribution. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
