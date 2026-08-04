# Reasoning and result

Half the switching frequency is not a defensible default crossover. Sampling, PWM delay, right-half-plane behavior where applicable, output-filter poles, ESR zeros, and layout parasitics constrain bandwidth. Measure or identify the plant across operating points, select a conservative crossover below unmodeled dynamics, design compensation, and verify gain/phase margin with loop injection plus load-step tests on hardware.

It makes the calculation or causal chain explicit before giving the recommendation. A predeclared decision threshold prevents the analysis from moving after results are seen. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
