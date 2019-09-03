#!/usr/bin/env python3
import itertools
import numpy as np 

from qat.lang.AQASM import *
import qat.core.task as task
import qat.core.qpu.agent as agent
import qat.core.qpu.stateanalyzer as stateanalyzer
import qat.core.qpu as qpu
import qat.linalg

import qat.core.circ as circ

nbqubits=9

errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(circuit, qubits, inputValue):
  # if inputValue == 1:
  #   circuit.apply(X, qubits[0])
  circuit.apply(Rz, inputValue['theta'])
  circuit.apply(Rx, inputValue['phi'])
  circuit.apply(H, qubits[0])

def BitFlipEncode(circuit, qubits, indices):
  circuit.apply(CNOT, qubits[indices[0]], qubits[indices[1]])
  circuit.apply(CNOT, qubits[indices[0]], qubits[indices[2]])

def PhaseFlipEncode(circuit, qubits, indices):
  BitFlipEncode(circuit, qubits, indices)
  for idx in indices:
    circuit.apply(H, qubits[idx])

def ErrorIntroduction(circuit, qubits, bitErrors):
  for err in bitErrors:
    circuit.apply(X, qubits[err])
    circuit.apply(Z, qubits[err])

def BitFlipDecode(circuit, qubits, indices):
  circuit.apply(CNOT, qubits[indices[0]], qubits[indices[1]])
  circuit.apply(CNOT, qubits[indices[0]], qubits[indices[2]])
  circuit.apply(CCNOT, qubits[indices[2]], qubits[indices[1]], qubits[indices[0]])

def PhaseFlipDecode(circuit, qubits, indices):
  for idx in indices:
    circuit.apply(H, qubits[idx])
  BitFlipDecode(circuit, qubits, indices)

def createProgram(inputValue, errorIdxs):
  circuit = Program()
  qubits=circuit.qalloc(nbqubits)
  PrepareState(circuit, qubits, inputValue)
  PhaseFlipEncode(circuit, qubits, [0, 3, 6])
  BitFlipEncode(circuit, qubits, [0, 1, 2])
  BitFlipEncode(circuit, qubits, [3, 4, 5])
  BitFlipEncode(circuit, qubits, [6, 7, 8])

  ErrorIntroduction(circuit, qubits, errorIdxs)

  BitFlipDecode(circuit, qubits, [6, 7, 8])
  BitFlipDecode(circuit, qubits, [3, 4, 5])
  BitFlipDecode(circuit, qubits, [0, 1, 2])
  PhaseFlipDecode(circuit, qubits, [0, 3, 6])

  circuit.apply(H, qubits[0])
  circuit.measure(qubits)
  circ.writecirc(circuit.to_circ(), "output.circ")
  return circuit

def runCircuit(circuit):
  circCircuit=circuit.to_circ("error_correction_"+repr(nbqubits))
  # # Executing the circuit
  simulator=qat.linalg.LinAlg()
  # Plugins :
  handlers = {'agent': agent.GenericAgent, 'state_analyzer': stateanalyzer.StateAnalyzer}
  qpu_handler = qpu.Server(simulator,handlers=handlers)

  mytask = task.Task(circCircuit)
  mytask.attach(qpu_handler)
  rangeset = range(nbqubits)
  return mytask.states(list(rangeset))

def printResults(results):
  for result in results:
    print("From states result returned "
      "state=%s ampl=%s proba=%s" % (result.state,
        result.amplitude,
        result.probability))

def testErrorCorrection():
  inputValues = [ #{'theta': 0, 'phi': 0}, # |0>
                 {'theta': math.pi / 2, 'phi': 0}, # |1>
                 {'theta': math.pi / 4, 'phi': 0}, # 1/sqrt(2) * ( |0> + |1> )
                 {'theta': math.pi / 4, 'phi': 2}, # Phase should not matter
                 {'theta': math.pi / 3, 'phi': 4}] # Uneven superposition
  for inputValue in inputValues: #range(2):
    print("Using input value " + str(inputValue))
    allErrorIdxs = []
    for nrOfErrors in range(2):
      allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
    # iterate over all possible combinations of errors
    for errorIdxs in allErrorIdxs:
      circuit = createProgram(inputValue, errorIdxs)
      results = list(runCircuit(circuit))
      prob_0 = 0.0
      prob_1 = 0.0
      for result in results:
        print(result)
        fullAmplitude = False
        if (str(result.amplitude) == "(1+0j)" or str(result.amplitude) == "(-1+0j)"):
          fullAmplitude = True
          testFailed = False
          if (inputValue == 0 and str(result.state)[:2] == "|0" or
            inputValue == 1 and str(result.state)[:2] == "|1"):
            print("Error correction worked. ", end="")
          else:
            print("Error correction wrong. ", end="")
            if len(errorIdxs) <= 1:
              testFailed = True
          print(str(result.state), end="")
          if testFailed:
            print(" With " + str(len(errorIdxs)) + " qubit-errors => TEST FAILED!")
          else:
            if len(errorIdxs) <= 1:
              print(" Test successful.")
            else:
              print("")
        if not fullAmplitude:
          print("No state with probability 1!")

testErrorCorrection()