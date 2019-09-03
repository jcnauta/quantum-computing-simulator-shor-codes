#!/usr/bin/env python3

from projectq import MainEngine
from projectq import ops

eng = MainEngine()
qubits = eng.allocate_qureg(3)
ops.CNOT | (qubits[0], qubits[1])
ops.CNOT | (qubits[0], qubits[2])
# Errors could have been introduced at this point,
# these would normally have to be corrected here.
ops.Measure | qubits[0]
eng.flush() # flush gates and perform measurement
print(int(qubits[0]))