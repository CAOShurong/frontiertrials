# Evidence-bounded answer

Half the switching frequency is not a defensible default crossover. Sampling, PWM delay, right-half-plane behavior where applicable, output-filter poles, ESR zeros, and layout parasitics constrain bandwidth. Measure or identify the plant across operating points, select a conservative crossover below unmodeled dynamics, design compensation, and verify gain/phase margin with loop injection plus load-step tests on hardware.

It separates supported conclusions from unresolved evidence in a short audit trail. The final decision remains conditional on the missing measurement. Record the exact interface, settings, timestamps, and raw observations so the result can be audited later.
