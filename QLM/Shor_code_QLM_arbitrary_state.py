#!/usr/bin/env python3
import itertools
import numpy as np 
import math

from qat.lang.AQASM import *
import qat.core.task as task
import qat.core.qpu.agent as agent
import qat.core.qpu.stateanalyzer as stateanalyzer
import qat.core.qpu as qpu
import qat.linalg

import qat.core.circ as circ

import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from shor_common.statevec_util import *

nbqubits=9

errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(circuit, qubits, inputValue):
  circuit.apply(RX(inputValue['theta']), qubits[0])
  circuit.apply(RZ(inputValue['phi']), qubits[0])
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
  # In reality we would measure, but since this is a simulation we can check the quantum state of the output.
  # circuit.measure(qubits)
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

def approxEqual(x, y, tolerance=0.00001):
    return (np.abs(x) < tolerance and np.abs(y) < tolerance) or np.abs(x-y) <= 0.5 * np.abs(x + y) * tolerance

def isCosPlusSin(phaseDiff):
  # The phase difference should be in the form cos(phi) + i sin(phi)
  if     phaseDiff.real < -1 or phaseDiff.real > 1 \
      or phaseDiff.imag < -1 or phaseDiff.imag > 1:
    print("Error: complex component of " + str(phaseDiff) + " out of bounds")
    return False
  phiReal = math.acos(phaseDiff.real) # or -phiImag.      Range is [0, PI]
  phiImag = math.asin(phaseDiff.imag) # or PI - phiImag   Range is [-PI/2, PI/2]

  if approxEqual((phiReal - phiImag) % math.pi, 0.0) or approxEqual((phiReal - phiImag) % math.pi, math.pi) or \
     approxEqual((-phiReal - phiImag) % math.pi, 0.0) or approxEqual((-phiReal - phiImag) % math.pi, math.pi) or \
     approxEqual((phiReal - (math.pi - phiImag)) % math.pi, 0.0) or approxEqual((phiReal - (math.pi - phiImag)) % math.pi, 0.0) or \
     approxEqual((-phiReal - (math.pi - phiImag)) % math.pi, 0.0) or approxEqual((-phiReal - (math.pi - phiImag)) % math.pi, 0.0):
    return True # phaseDiffA0 not of the form cos(phi) + i sin(phi)
  else:
    return False

def sameState(psiA, psiB):
  # amplitudes must be the same, up to a global phase.
  psiA0, psiA1 = psiA[0], psiA[1]
  psiB0, psiB1 = psiB[0], psiB[1]
  # The phase difference to multiply state psiA with so that its amplitude
  # is equal to that of psiB.
  phaseDiff = None
  basedOnEigen = None # will be 0 or 1, depending on which complex amplitude is used to calculate phaseDiff
  if np.abs(psiA0) >= np.abs(psiA1):
    phaseDiff = psiB0 / psiA0
    basedOnEigen = 0
  elif np.abs(psiA0) <= np.abs(psiA1):
    phaseDiff = psiB1 / psiA1
    basedOnEigen = 1

  # The phase difference should be in the form cos(phi) + i sin(phi)
  phaseDiff = clampedComponents(phaseDiff)
  if not isCosPlusSin(phaseDiff):
    print("Not e^(i*phi)")
    return False

  # Finally check that the phase difference for the other eigenstate is the same
  if    basedOnEigen == 0 and approxEqual(psiA1 * phaseDiff, psiB1) \
     or basedOnEigen == 1 and approxEqual(psiA0 * phaseDiff, psiB0):
    return True
  else:
    print("Phases not equal: ")
    return False

def stateForInput(th, ph):
  ampl0 = complex(math.cos(ph/2) * math.cos(th/2), math.sin(ph/2) * math.cos(th/2) * -1)
  ampl1 = complex(math.sin(ph/2) * math.sin(th/2), math.cos(ph/2) * math.sin(th/2) * -1)
  return [ampl0, ampl1]

def clampedComponents(ampl):
  comps = [ampl.real, ampl.imag]
  for compIdx in [0, 1]:
    c = comps[compIdx]
    if c < -1.0:
      if approxEqual(c, -1.0):
        comps[compIdx] = -1.0
      else:
        print("Error: complex amplitude magnitude too large (negative).")
        exit()
    if c > 1.0:
      if approxEqual(c, 1.0):
        comps[compIdx] = 1.0
      else:
        print("Error: complex amplitude magnitude too large (positive).")
        exit()
  return complex(comps[0], comps[1])

def clampedAmplitudes(state):
  clampedState = [complex(), complex()]
  for eigenstateIdx in [0, 1]:
    ampl = state[eigenstateIdx]
    clampedState[eigenstateIdx] = clampedComponents(ampl)
  return clampedState

def testErrorCorrection():
  # Bloch sphere angles
  inputValues = [{'theta': 0, 'phi': 0}, # |0>
                 {'theta': math.pi, 'phi': 0}, # |1>
                 {'theta': math.pi / 2, 'phi': 0}, # 1/sqrt(2) * ( |0> + |1> )
                 {'theta': math.pi / 2, 'phi': 2}, # Phase should not matter
                 {'theta': math.pi * 2 / 3, 'phi': 4}] # Uneven superposition
  failures = 0
  for inputValue in inputValues: #range(2):
    print("Using input value " + str(inputValue))
    allErrorIdxs = []
    for nrOfErrors in range(2):
      allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
    # iterate over all possible combinations of errors
    inputStateComplex = stateForInput(inputValue['theta'], inputValue['phi'])
    for errorIdxs in allErrorIdxs:
      circuit = createProgram(inputValue, errorIdxs)
      results = list(runCircuit(circuit))
      ampl0 = complex()
      ampl1 = complex()
      # Result for each possible 9-qubit eigenstate
      # If all went well there is only one (non-zero amplitude) end state
      # with first qubit 0, and one with first qubit 1.
      # Adding up all amplitudes gives us the amplitudes of these two states.
      for result in results:
        resultBit = result.state[0]
        if resultBit == False:
          ampl0 += result.amplitude
        elif resultBit == True:
          ampl1 += result.amplitude
        else:
          print("Error: expected either 0 or 1 as a result bit.")
          exit()
      inputStateComplex = clampedAmplitudes(inputStateComplex)
      clampedAmpls = clampedAmplitudes([ampl0, ampl1])
      if sameState(inputStateComplex, clampedAmpls):
        print("    Error correction worked. Test succesful.")
      else:
        failures += 1
        print("    Error correction wrong.\n"
            + "    Expected ampl(0) = " + str(inputStateComplex[0]) + ", got " + str(ampl0) + "\n"
            + "    Expected p(1) = " + str(inputStateComplex[1]) + ", got " + str(ampl1))
  if failures > 0:
    print("Error: test failed!")
  else:
    print("Success: all tests passed!")

testErrorCorrection()