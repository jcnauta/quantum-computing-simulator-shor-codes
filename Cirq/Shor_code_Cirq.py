#!/usr/bin/env python3.5
# Shor-code implementation for cirQ

import cirq
import numpy as np
import itertools

nbqubits = 9

def PrepareState(circuit, qubits, inputValue):
  circuit.append([
                  cirq.Rx(inputValue['theta'])(qubits[0]),
                  cirq.Rz(inputValue['phi'])(qubits[0])
                 ])

def BitFlipEncode(circuit, qubits, indices):
  circuit.append([cirq.CNOT(qubits[indices[0]], qubits[indices[1]]),
                  cirq.CNOT(qubits[indices[0]], qubits[indices[2]])])
  
def PhaseFlipEncode(circuit, qubits, indices):
  BitFlipEncode(circuit, qubits, indices)
  for idx in indices:
    circuit.append(cirq.H(qubits[idx]))
    
def ErrorIntroduction(circuit, qubits, bitErrors):
  for err in bitErrors:
    circuit.append([cirq.X(qubits[err]),
                  cirq.Z(qubits[err])])
  
def BitFlipDecode(circuit, qubits, indices):
  circuit.append([cirq.CNOT(qubits[indices[0]], qubits[indices[1]]),
                  cirq.CNOT(qubits[indices[0]], qubits[indices[2]]),
                  cirq.TOFFOLI(qubits[indices[2]], qubits[indices[1]], qubits[indices[0]])])
 
def PhaseFlipDecode(circuit, qubits, indices):
  for idx in indices:
    circuit.append(cirq.H(qubits[idx]))
  BitFlipDecode(circuit, qubits, indices)
  
def createProgram(nbqubits, inputValue, errorIdxs):
  qubits = [cirq.GridQubit(0,i) for i in range(nbqubits)]
  circuit = cirq.Circuit()
  
  PrepareState(circuit, qubits, inputValue)
  
  PhaseFlipEncode(circuit, qubits, [0,3,6])
  BitFlipEncode(circuit, qubits, [0,1,2])
  BitFlipEncode(circuit, qubits, [3,4,5])
  BitFlipEncode(circuit, qubits, [6,7,8])
  
  ErrorIntroduction(circuit, qubits, errorIdxs)
  
  BitFlipDecode(circuit, qubits, [0,1,2])
  BitFlipDecode(circuit, qubits, [3,4,5])
  BitFlipDecode(circuit, qubits, [6,7,8])
  PhaseFlipDecode(circuit, qubits, [0,3,6])
  
  circuit.append(cirq.measure(qubits[0], key='quantum state'))
  return circuit

def _stateForInput(th, ph):
  ampl0 = complex(np.cos(ph/2) * np.cos(th/2), np.sin(ph/2) * np.cos(th/2) * -1)
  ampl1 = complex(np.sin(ph/2) * np.sin(th/2), np.cos(ph/2) * np.sin(th/2) * -1)
  return [ampl0, ampl1]
  
def testErrorCorrection():
  numShots = 1024
  inputValues = [{'theta': 0, 'phi': 0}, #|0>
                 {'theta': np.pi, 'phi': np.pi}, #|1>
                 {'theta': np.pi/2, 'phi': np.pi/2} #|+>
                ]
                
  for inputValue in inputValues:
    print("Using input value "+str(inputValue))
    allErrorIdxs = []
    for nrOfErrors in range(2):
      allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
    
    for errorIdxs in allErrorIdxs:
      inputStateComplex = _stateForInput(inputValue['theta'], inputValue['phi'])
      
      result = createProgram(nbqubits, inputValue, errorIdxs)
      result = cirq.Simulator().run(result, repetitions=numShots)
      
      prob_0 = 0
      prob_1 = 0
      for i in range(numShots):
        if result.measurements['quantum state'][i][0] == 0:
          prob_0 += 1
        else:
          prob_1 += 1
      prob_0 /= numShots
      prob_1 /= numShots
      
      if abs(prob_0 - abs(inputStateComplex[0])**2) < 0.0001 and abs(prob_1 - abs(inputStateComplex[1])**2) < 0.0001:
        print("Error correction works")
      else:
        print("Error correction fails")
        print("Might be due to simulation results, instead of probability distributions")
        print("Found probabilities are:", prob_0, "and", prob_1)
        

testErrorCorrection()