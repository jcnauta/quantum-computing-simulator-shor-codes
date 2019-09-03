# Shor-code implementation for PyQuil

import pyquil#from pyquil import qet_qc
from pyquil.quil import Program
from pyquil.api import WavefunctionSimulator, local_qvm
import pyquil.gates as ops

import numpy as np 
import itertools

nbqubits = 9

def PrepareState(inputValue):
  return [ops.RX(inputValue['theta'], 0), ops.RZ(inputValue['phi'], 0)]
  
def BitFlipEncode(indices):
  return [ops.CNOT(indices[0], indices[1]),
          ops.CNOT(indices[0], indices[2])]

def PhaseFlipEncode(indices):
  p = BitFlipEncode(indices)
  for idx in indices:
    p += [ops.H(idx)]
  return p

def ErrorIntroduction(bitErrors):
  prog = []
  for err in bitErrors:
    prog += [ops.X(err), ops.Z(err)]
  return prog
  
def BitFlipDecode(indices):
  return [ops.CNOT(indices[0], indices[1]),
          ops.CNOT(indices[0], indices[2]),
          ops.CCNOT(indices[2], indices[1], indices[0])]

def PhaseFlipDecode(indices):
  p = []
  for idx in indices:
    p += [ops.H(idx)]
  return p + BitFlipDecode(indices)
  
def createProgram(inputValue, errorIdxs):
  p = Program()
  #ro = p.declare('ro', memory_type='BIT', memory_size=2)
  
  p += PrepareState(inputValue)
  
  p += PhaseFlipEncode([0,3,6])
  p += BitFlipEncode([0,1,2])
  p += BitFlipEncode([3,4,5])
  p += BitFlipEncode([6,7,8])
  
  p += ErrorIntroduction(errorIdxs)
  
  p += BitFlipDecode([0,1,2])
  p += BitFlipDecode([3,4,5])
  p += BitFlipDecode([6,7,8])
  p += PhaseFlipDecode([0,3,6])
  
  return p

def _stateForInput(th, ph):
  ampl0 = complex(np.cos(ph/2) * np.cos(th/2), np.sin(ph/2) * np.cos(th/2) * -1)
  ampl1 = complex(np.sin(ph/2) * np.sin(th/2), np.cos(ph/2) * np.sin(th/2) * -1)
  return [ampl0, ampl1]

def testErrorCorrection():
  qc = pyquil.get_qc('9q-qvm') # Note that this one has a topology
  p = Program()
  ro = p.declare('ro', memory_type='BIT', memory_size=1)
  
  num_trials = 100
  
  inputValues = [{'theta': 0, 'phi': 0}, #|0>
                 {'theta': np.pi, 'phi': np.pi}, #|1>
                 {'theta': np.pi/2, 'phi': np.pi/2} #|+>
                ]
  for inputValue in inputValues:
    print("Using input value", inputValue)
    allErrorIdxs = []
    
    for nrOfErrors in range(2):
      allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
      # iterate over all possible combinations of errors
    
    for errorIdxs in allErrorIdxs:
      inputStateComplex = _stateForInput(inputValue['theta'], inputValue['phi'])
        
      print("Introducing errors, indices " + str(errorIdxs))
      program = createProgram(inputValue, errorIdxs)
      
      prob_0 = 0
      prob_1 = 0
      
      if 1: # Wavefunction
        wf_sim = WavefunctionSimulator()
          
        wavefunction = wf_sim.wavefunction(program)
          
        result = wavefunction.pretty_print_probabilities()
        
        for key, value in zip(result.keys(), result.values()):
          if key[-1] == '0':
            prob_0 += value
          else:
            prob_1 += value
      else: # Using measurements
        result = qc.run_and_measure(program, trials=num_trials)
        prob_0 += np.sum(result[0] == 0) / num_trials
        prob_1 += np.sum(result[0] == 1) / num_trials
        
      if abs(prob_0 - abs(inputStateComplex[0])**2) < 0.0001 and abs(prob_1 - abs(inputStateComplex[1])**2) < 0.0001:
        print("Error correction works")
      else: 
        print("Error correction failed")

 
res = testErrorCorrection()


