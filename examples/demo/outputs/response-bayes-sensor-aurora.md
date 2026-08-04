# Recommended approach

For 10,000 units, expect 50 faults: about 47 positive alerts among faults. Of 9,950 healthy units, a 3% false-positive rate gives about 298.5 positive alerts. The positive predictive value is 47 / (47 + 298.5) = 0.136, or about 13.6%. A positive alert should trigger a confirmatory test rather than automatic replacement because most positives are false at this low base rate.

It uses a compact decision tree and explicit stop conditions. The main limitation is that each branch needs repeated measurements before attribution. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
