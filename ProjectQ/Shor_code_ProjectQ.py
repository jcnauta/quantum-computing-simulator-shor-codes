#!/usr/bin/env python3
# Shor-code implementation for ProjectQ

from projectq import MainEngine
from projectq import ops

import itertools
import numpy as np 

nbqubits = 9
errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(qubits, inputValue):
  ops.Rx(inputValue['theta']) | qubits[0]
  ops.Rz(inputValue['phi']) | qubits[0]

def BitFlipEncode(qubits, indices):
  ops.CNOT | (qubits[indices[0]], qubits[indices[1]])
  ops.CNOT | (qubits[indices[0]], qubits[indices[2]])

def PhaseFlipEncode(qubits, indices):
  BitFlipEncode(qubits, indices)
  for idx in indices:
      ops.H | qubits[idx]

def ErrorIntroduction(qubits, bitErrors):
  for err in bitErrors:
      ops.X | qubits[err]
      ops.Z | qubits[err]
  
def BitFlipDecode(qubits, indices):
  ops.CNOT | (qubits[indices[0]], qubits[indices[1]])
  ops.CNOT | (qubits[indices[0]], qubits[indices[2]])
  ops.Toffoli | (qubits[indices[2]], qubits[indices[1]], qubits[indices[0]])
 
def PhaseFlipDecode(qubits, indices):
  for idx in indices:
      ops.H | qubits[idx]
  BitFlipDecode(qubits, indices)
  
def createProgram(qubits, inputValue, errorIdxs):
  PrepareState(qubits, inputValue)
  
  PhaseFlipEncode(qubits, [0,3,6])
  BitFlipEncode(qubits, [0,1,2])
  BitFlipEncode(qubits, [3,4,5])
  BitFlipEncode(qubits, [6,7,8])
  
  ErrorIntroduction(qubits, errorIdxs)
  
  BitFlipDecode(qubits, [0,1,2])
  BitFlipDecode(qubits, [3,4,5])
  BitFlipDecode(qubits, [6,7,8])
  PhaseFlipDecode(qubits, [0,3,6])
  
  ops.Measure | qubits[0] # Only the first bit is of importance. All others are to encode the state
  ops.All(ops.Measure) | qubits[1:] # All other qubits should be zero
  
  return qubits

def _stateForInput(th, ph):
  ampl0 = complex(np.cos(ph/2) * np.cos(th/2), np.sin(ph/2) * np.cos(th/2) * -1)
  ampl1 = complex(np.sin(ph/2) * np.sin(th/2), np.cos(ph/2) * np.sin(th/2) * -1)
  return [ampl0, ampl1]

def testErrorCorrection():
  num_shots = 20
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
      
      prob_0 = 0
      prob_1 = 0
      
      #Note multiple shots are not possible
      for _ in range(num_shots):
          eng = MainEngine()
          qubits = eng.allocate_qureg(nbqubits)
      
          qubits = createProgram(qubits, inputValue, errorIdxs)
          print(int(qubits[0]))
          if (int(qubits[0]) == 0):
              prob_0 += 1
          else:
              prob_1 += 1
      prob_0 /= num_shots
      prob_1 /= num_shots
      if abs(prob_0 - abs(inputStateComplex[0])**2) < 0.0001 and abs(prob_1 - abs(inputStateComplex[1])**2) < 0.0001:
        print("Error correction works")
      else: 
        print("Error correction failed")
        print("This might be due to simulation results compared to theoretical results")
      
        
testErrorCorrection()

