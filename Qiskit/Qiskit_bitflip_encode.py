#!/usr/bin/env python3

import qiskit

def BitFlipEncode(circuit, qubits, cbits, indices):
  circuit.cx(qubits[indices[0]], qubits[indices[1]])
  circuit.cx(qubits[indices[0]], qubits[indices[2]])

nbqubits = 3
qubits = qiskit.QuantumRegister(nbqubits, 'q')
cbits = qiskit.ClassicalRegister(nbqubits, 'b')
circuit = qiskit.QuantumCircuit(qubits, cbits, name='Shor code')
BitFlipEncode(circuit, qubits, cbits, [0, 1, 2])
# Errors could be introduced and should be corrected here
circuit.measure(qubits[0], cbits[0])

backend = qiskit.Aer.get_backend('statevector_simulator')
job = qiskit.execute(circuit, backend)
result = job.result()
print(result.get_statevector(circuit))
