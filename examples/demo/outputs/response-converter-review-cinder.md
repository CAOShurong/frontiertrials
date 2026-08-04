# Practical checklist

Half the switching frequency is not a defensible default crossover. Sampling, PWM delay, right-half-plane behavior where applicable, output-filter poles, ESR zeros, and layout parasitics constrain bandwidth. Measure or identify the plant across operating points, select a conservative crossover below unmodeled dynamics, design compensation, and verify gain/phase margin with loop injection plus load-step tests on hardware.

It prioritizes a concise checklist that can be used at the bench. Some implementation detail should still be fixed in the lab record. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
