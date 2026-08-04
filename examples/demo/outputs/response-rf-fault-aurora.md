# Recommended approach

Start by reproducing the speed-correlated loss with a fixed receiver configuration. Capture supply ripple and a spectrum trace while stepping motor speed. Test conducted coupling by powering the motor separately, then test radiated coupling with distance, orientation, and near-field scans. Change one variable at a time. Stop when the sensitivity loss follows one coupling path and the mitigation restores the baseline in repeated runs.

It uses a compact decision tree and explicit stop conditions. The main limitation is that each branch needs repeated measurements before attribution. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
