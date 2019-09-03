#!/usr/bin/env python3

import os
import sys
import math
import itertools


# Add the qubiter repository to the PATH to import modules.
os.chdir('qubiter')
sys.path.insert(0,os.getcwd())

from SEO_writer import *
from SEO_simulator import *
from StateVec import *
import numpy as np

nbqubits=9

errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(wr, inputValue):
  # Use negative half-angles (Qubiter's apparent convention).
  wr.write_Rx(0, -0.5 * inputValue['theta'])
  wr.write_Rz(0, -0.5 * inputValue['phi'])

def BitFlipEncode(wr, indices):
  wr.write_cnot(control_bit=indices[0], target_bit=indices[1])
  wr.write_cnot(control_bit=indices[0], target_bit=indices[2])

def PhaseFlipEncode(wr, indices):
  BitFlipEncode(wr, indices)
  for idx in indices:
    wr.write_H(idx)

def ErrorIntroduction(wr, bitErrors):
  for err in bitErrors:
    wr.write_X(err)
    wr.write_Z(err)

def BitFlipDecode(wr, indices):
  wr.write_cnot(indices[0], indices[1])
  wr.write_cnot(indices[0], indices[2])
  controls = Controls(nbqubits)
  controls.bit_pos_to_kind = {indices[1]: True, indices[2]: True}
  controls.refresh_lists()
  wr.write_controlled_one_bit_gate(indices[0], controls, OneBitGates.sigx)

def PhaseFlipDecode(wr, indices):
  for idx in indices:
    wr.write_H(idx)
  BitFlipDecode(wr, indices)

def createProgram(inputValue, errorIdxs):
  emb = CktEmbedder(nbqubits, nbqubits)
  file_prefix = 'io_folder/repetition_code_qubiter_' + str(inputValue) + '_err_idxs' + '-'.join(map(lambda x: str(x), errorIdxs))
  wr = SEO_writer(file_prefix, emb)
  PrepareState(wr, inputValue)

  PhaseFlipEncode(wr, [0, 3, 6])
  BitFlipEncode(wr, [0, 1, 2])
  BitFlipEncode(wr, [3, 4, 5])
  BitFlipEncode(wr, [6, 7, 8])

  ErrorIntroduction(wr, errorIdxs)

  BitFlipDecode(wr, [6, 7, 8])
  BitFlipDecode(wr, [3, 4, 5])
  BitFlipDecode(wr, [0, 1, 2])
  PhaseFlipDecode(wr, [0, 3, 6])

  for idx in range(nbqubits):
    wr.write_MEAS(idx, kind=2)
  wr.close_files()
  return file_prefix

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
    print("phaseDiff not in form e^(i*phi)")
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
  if not isCosPlusSin(phaseDiff):
    print("Not e^(i*phi)")
    return False

  # Finally check that the phase difference for the other eigenstate is the same
  if    basedOnEigen == 0 and approxEqual(psiA1 * phaseDiff, psiB1) \
     or basedOnEigen == 1 and approxEqual(psiB1 * phaseDiff, psiA1):
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
        print("Error: complex amplitude magnitude too large (negative): " + str(c))
        exit()
    if c > 1.0:
      if approxEqual(c, 1.0):
        comps[compIdx] = 1.0
      else:
        print("Error: complex amplitude magnitude too large (positive): " + str(c))
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
                   {'theta': math.pi, 'phi': math.pi}, # |1>
                   {'theta': math.pi / 2, 'phi': math.pi / 2}, # Uniform superposition
                   {'theta': math.pi / 2, 'phi': 2}, # Abnormal phase
                   {'theta': math.pi * 2 / 3, 'phi': 4}] # Abnormal superposition
    failures = 0
    for inputValue in inputValues:
        print("Using input value " + str(inputValue))
        allErrorIdxs = []
        for nrOfErrors in range(2):
            allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
        # iterate over all possible combinations of errors
        for errorIdxs in allErrorIdxs:
            # print("    Introducing errors, indices " + str(errorIdxs))
            file_prefix = createProgram(inputValue, errorIdxs)
            # pic_file = file_prefix + '_' + str(nbqubits) + '_ZLpic.txt'
            # with open(pic_file) as f:
            #     print(f.read())
            init_st_vec = StateVec.get_standard_basis_st_vec([0, 0, 0, 0, 0, 0, 0, 0, 0])
            sim = SEO_simulator(file_prefix, nbqubits, init_st_vec)

            inputStateComplex = stateForInput(inputValue['theta'], inputValue['phi'])
            # print("Input state complex = " + str(inputStateComplex))
            prob_0 = 0.0
            prob_1 = 0.0
            ampl0 = complex()
            ampl1 = complex()
            for _, stateVec in sim.cur_st_vec_dict.items():
              # There are 2^nbqubits stateVecs, but most do not have an associated array.
              # This has to to with doing type 2 (rather than type 0 or type 1) measurements.
              if stateVec.arr is not None:
                states = stateVec.get_traditional_st_vec()
                for stateIdx in range(len(states)):
                  stateProb = np.absolute(states[stateIdx]) ** 2
                  # This is one of our final states, check if our original bit has been corrected.
                  # With successful correction, the final state is identical to the initial state
                  # except for a global phase difference.
                  stateBinary = np.binary_repr(stateIdx, width=nbqubits)
                  if stateProb > 0.0001:
                  #   print("    " + str(stateBinary) + " with amplitude " + str(states[stateIdx]))
                    resultQubit = stateBinary[nbqubits - 1]
                    if resultQubit == '0':
                      ampl0 = states[stateIdx]
                      prob_0 = stateProb
                    elif resultQubit == '1':
                      ampl1 = states[stateIdx]
                      prob_1 = stateProb
                    else:
                      print("Expected 0 or 1 as last digit of binary state representation.")
                      exit()
            # print("prob 0 = " + str(prob_0))
            # print("prob 1 = " + str(prob_1))
            inputStateComplex = clampedAmplitudes(inputStateComplex)
            clampedAmpls = clampedAmplitudes([ampl0, ampl1])
            if sameState(inputStateComplex, clampedAmpls):
              print("    Error correction worked. Test succesful.")
            else:
              failures += 1
              print("Input state complex = " + str(inputStateComplex))
              print("    Error correction wrong.\n"
                  + "    Expected amp(0) = " + str(inputStateComplex[0]) + ", got " + str(ampl0) + "\n"
                  + "    Expected amp(1) = " + str(inputStateComplex[1]) + ", got " + str(ampl1))
    if failures > 0:
      print("Error: test failed!")
    else:
      print("Success: all tests passed!")

testErrorCorrection()