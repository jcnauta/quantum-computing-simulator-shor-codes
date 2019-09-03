# Shor-code implementation for Qiskit

import qiskit

import numpy as np
import itertools
import math

nbqubits = 9
errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(circuit, qubits, inputValue):
  if inputValue == 1:
    circuit.x(qubits[0])
  circuit.h(qubits[0])

def BitFlipEncode(circuit, qubits, indices):
  circuit.cx(qubits[indices[0]], qubits[indices[1]])
  circuit.cx(qubits[indices[0]], qubits[indices[2]])

def PhaseFlipEncode(circuit, qubits, indices):
  circuit.h(qubits[indices[0]])
  BitFlipEncode(circuit, qubits, indices)

def ErrorIntroduction(circuit, qubits, errorIdxs):
  for err in errorIdxs:
    circuit.x(qubits[err])
    circuit.z(qubits[err])
  
def BitFlipDecode(circuit, qubits, indices):
  circuit.cx(qubits[indices[0]], qubits[indices[1]])
  circuit.cx(qubits[indices[0]], qubits[indices[2]])
  circuit.ccx(qubits[indices[2]], qubits[indices[1]], qubits[indices[0]])

def PhaseFlipDecode(circuit, qubits, indices):
  BitFlipDecode(circuit, qubits, indices)
  circuit.h(qubits[indices[0]])
  
def createProgram(inputValue, errorIdxs):
  nqubits = 9
  qubits = qiskit.QuantumRegister(nqubits, 'q')
  binary = qiskit.ClassicalRegister(nqubits, 'b')
  circuit = qiskit.QuantumCircuit(qubits, binary, name='Shor-code')
  
  PrepareState(circuit, qubits, inputValue)
  
  BitFlipEncode(circuit, qubits, [0,3,6])
  PhaseFlipEncode(circuit, qubits, [0,1,2])
  PhaseFlipEncode(circuit, qubits, [3,4,5])
  PhaseFlipEncode(circuit, qubits, [6,7,8])
  
  ErrorIntroduction(circuit, qubits, errorIdxs)
  
  PhaseFlipDecode(circuit, qubits, [0,1,2])
  PhaseFlipDecode(circuit, qubits, [3,4,5])
  PhaseFlipDecode(circuit, qubits, [6,7,8])
  BitFlipDecode(circuit, qubits, [0,3,6])
  
  circuit.h(qubits[0])

  # Only the first bit is of importance. All others are to encode the state
  # circuit.measure(qubits[0],binary[0])
  return circuit

def _approxEqual(x, y, tolerance=0.00001):
    return (x < tolerance and y < tolerance) or abs(x-y) <= 0.5 * (x + y) * tolerance

def testErrorCorrection():
  # inputValues = [{'theta': 0, 'phi': 0}, # |0>
  #                  {'theta': math.pi / 2, 'phi': 0}, # |1>
  #                  {'theta': math.pi / 4, 'phi': 0}, # 1/sqrt(2) * ( |0> + |1> )
  #                  {'theta': math.pi / 4, 'phi': 2}, # Phase should not matter
  #                  {'theta': math.pi / 3, 'phi': 4}] # Uneven superposition
  failures = 0
  for inputValue in range(2): #inputValues:
      print("Using input value " + str(inputValue))
      allErrorIdxs = []
      for nrOfErrors in range(2):
          allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
      # iterate over all possible combinations of errors
      for errorIdxs in allErrorIdxs:
        print("    Introducing errors, indices " + str(errorIdxs))
        # print("Creating program, introducing errors at indices " + str(errorIdxs))
        circuit = createProgram(inputValue, errorIdxs)
        # statevector_simulator for full state, to emulate with e.g. noise use qasm_simulator
        backend = qiskit.Aer.get_backend('statevector_simulator')
        job = qiskit.execute(circuit, backend, shots=100)
        result = job.result()
        prob_0 = 0.0
        prob_1 = 0.0
        # There are 2^nbqubits stateVecs, but most do not have an associated array.
        # This has to to with doing type 2 (rather than type 0 or type 1) measurements.
        fullAmplitude = False
        stateVec = result.get_statevector(circuit)
        for stateIdx in range(len(stateVec)):
          stateProb = np.absolute(stateVec[stateIdx]) ** 2
          stateBinary = np.binary_repr(stateIdx, width=nbqubits)
          resultQubit = stateBinary[nbqubits - 1]
          # if stateProb > 0.0001:
          #   print("    " + str(stateBinary) + " with amplitude " + str(stateVec[stateIdx]))
          if resultQubit == '0':
            prob_0 += stateProb
          elif resultQubit == '1':
            prob_1 += stateProb
          else:
            print("Expected 0 or 1 as last digit of binary state representation.")
            exit()
        prob_0_correct = 0 if inputValue == 1 else 1
        prob_1_correct = inputValue
        if _approxEqual(prob_0, prob_0_correct) and _approxEqual(prob_1, prob_1_correct):
          print("    Error correction worked. Test succesful.")
        else:
          failures += 1
          print("    Error correction wrong.\n"
              + "    Expected p(0) = " + str(prob_0_correct) + ", got " + str(prob_0) + "\n"
              + "    Expected p(1) = " + str(prob_1_correct) + ", got " + str(prob_1))
  if failures > 0:
    print("Error: test failed!")
  else:
    print("Success: all tests passed!")

testErrorCorrection()