#!/usr/bin/env python3


# Shor-code implementation for Qiskit

import qiskit

import numpy as np
import itertools
import math
import json
from qiskit import IBMQ

import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from shor_common.statevec_util import *

# With qiskit >= 0.11
# IBMQ.load_account()

# my_provider = IBMQ.get_provider()
# print(my_provider.backends())
# print(qiskit.Aer.backends())

# statevector_simulator for full state, to emulate with e.g. noise use qasm_simulator
backend = qiskit.Aer.get_backend('statevector_simulator')
# backend = my_provider.get_backend('ibmq_16_melbourne')
# backend = my_provider.get_backend('ibmq_qasm_simulator')

nbqubits = 9
errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(circuit, qubits, inputValue):
  circuit.rx(inputValue['theta'], qubits[0])
  circuit.rz(inputValue['phi'], qubits[0])

def BitFlipEncode(circuit, qubits, indices):
  circuit.cx(qubits[indices[0]], qubits[indices[1]])
  circuit.cx(qubits[indices[0]], qubits[indices[2]])

def PhaseFlipEncode(circuit, qubits, indices):
  BitFlipEncode(circuit, qubits, indices)
  for idx in indices:
    circuit.h(qubits[idx])

def ErrorIntroduction(circuit, qubits, errorIdxs):
  for err in errorIdxs:
    circuit.x(qubits[err])
    circuit.z(qubits[err])
  
def BitFlipDecode(circuit, qubits, indices):
  circuit.cx(qubits[indices[0]], qubits[indices[1]])
  circuit.cx(qubits[indices[0]], qubits[indices[2]])
  circuit.ccx(qubits[indices[2]], qubits[indices[1]], qubits[indices[0]])

def PhaseFlipDecode(circuit, qubits, indices):
  for idx in indices:
    circuit.h(qubits[idx])
  BitFlipDecode(circuit, qubits, indices)
  
def createProgram(inputValue, errorIdxs):
  nqubits = 9
  qubits = qiskit.QuantumRegister(nqubits, 'q')
  binary = qiskit.ClassicalRegister(nqubits, 'b')
  circuit = qiskit.QuantumCircuit(qubits, binary, name='Shor-code')
  
  PrepareState(circuit, qubits, inputValue)
  
  PhaseFlipEncode(circuit, qubits, [0, 3, 6])
  circuit.barrier(qubits)
  BitFlipEncode(circuit, qubits, [0, 1, 2])
  BitFlipEncode(circuit, qubits, [3, 4, 5])
  BitFlipEncode(circuit, qubits, [6, 7, 8])

  circuit.barrier(qubits)
  ErrorIntroduction(circuit, qubits, errorIdxs)
  circuit.barrier(qubits)

  BitFlipDecode(circuit, qubits, [6, 7, 8])
  BitFlipDecode(circuit, qubits, [3, 4, 5])
  BitFlipDecode(circuit, qubits, [0, 1, 2])
  circuit.barrier(qubits)
  PhaseFlipDecode(circuit, qubits, [0, 3, 6])

  # Only the first bit is of importance. All others are to encode the state
  # circuit.measure(qubits[0],binary[0])
  return circuit

def testErrorCorrection():
  # Bloch sphere angles
  inputValues = [{'theta': 0, 'phi': 0}, # |0>
                 {'theta': math.pi, 'phi': math.pi}, # |1>
                 {'theta': math.pi / 2, 'phi': 0}, # 1/sqrt(2) * ( |0> + |1> )
                 {'theta': math.pi / 2, 'phi': 2}, # Phase should not matter
                 {'theta': math.pi * 2 / 3, 'phi': 4}] # Uneven superposition
  failures = 0
  for inputValue in inputValues:
      print("Using input value " + str(inputValue))
      allErrorIdxs = []
      for nrOfErrors in range(2):
          allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
      # iterate over all possible combinations of errors
      for errorIdxs in allErrorIdxs:
        print("    Introducing errors, indices " + str(errorIdxs))
        # print("Creating program, introducing errors at indices " + str(errorIdxs))
        circuit = createProgram(inputValue, errorIdxs)
        # print(circuit) # uncomment for debugging
        job = qiskit.execute(circuit, backend, shots=100)
        result = job.result()
        inputStateComplex = stateForInput(inputValue['theta'], inputValue['phi'])
        amp0 = complex()
        amp1 = complex()
        # There are 2^nbqubits stateVecs, but most do not have an associated array.
        fullAmplitude = False
        stateVec = result.get_statevector(circuit)
        for stateIdx in range(len(stateVec)):
          stateProb = np.absolute(stateVec[stateIdx]) ** 2
          stateBinary = np.binary_repr(stateIdx, width=nbqubits)
          resultQubit = stateBinary[nbqubits - 1]
          if stateProb > 0.0001:
            print("    " + str(stateBinary) + " with amplitude " + str(stateVec[stateIdx]))
            # The input was a superposition of two states that only differed in the first qubit
            # These are each mapped to one output state, of which we wish to know the amplitude.
            if resultQubit == '0':
              amp0 = stateVec[stateIdx]
            elif resultQubit == '1':
              amp1 = stateVec[stateIdx]
            else:
              print("Expected 0 or 1 as last digit of binary state representation.")
              exit()
        if sameState([amp0, amp1], inputStateComplex):
          print("    Error correction worked. Test succesful.")
        else:
          failures += 1
          print("Input state complex = " + str(inputStateComplex))
          print("    Error correction wrong.\n"
              + "    Expected amp(0) = " + str(inputStateComplex[0]) + ", got " + str(amp0) + "\n"
              + "    Expected amp(1) = " + str(inputStateComplex[1]) + ", got " + str(amp1))
          exit()
  if failures > 0:
    print("Error: test failed!")
  else:
    print("Success: all tests passed!")

testErrorCorrection()