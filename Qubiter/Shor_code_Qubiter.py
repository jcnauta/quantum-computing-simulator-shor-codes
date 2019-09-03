#!/usr/bin/env python3

import os
import sys
import itertools


# Add the qubiter repository to the PATH to import modules.
print(os.getcwd())
os.chdir('qubiter')
print(os.getcwd())
sys.path.insert(0,os.getcwd())

from SEO_writer import *
from SEO_simulator import *
from StateVec import *
import numpy as np

nbqubits=9

errorProbability = 1
errorAngle = 2*np.arcsin(np.sqrt(errorProbability))

def PrepareState(wr, inputValue):
  if inputValue == 1:
    wr.write_X(0)
  wr.write_H(0)

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

  wr.write_H(0)
  for idx in range(nbqubits):
    wr.write_MEAS(idx, kind=2)
  return file_prefix

def testErrorCorrection():
    for inputValue in range(2):
        print("Using input value " + str(inputValue))
        allErrorIdxs = []
        for nrOfErrors in range(2):
            allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
        # iterate over all possible combinations of errors
        circuits = []
        for errorIdxs in allErrorIdxs:
            # print("Creating program, introducing errors at indices " + str(errorIdxs))
            file_prefix = createProgram(inputValue, errorIdxs)
            # pic_file = file_prefix + '_' + str(nbqubits) + '_ZLpic.txt'
            # with open(pic_file) as f:
            #     print(f.read())
            init_st_vec = StateVec.get_standard_basis_st_vec([0, 0, 0, 0, 0, 0, 0, 0, 0])
            sim = SEO_simulator(file_prefix, nbqubits, init_st_vec)

            oneState = False # Verify that we do not end up in a superposition.
            for _, stateVec in sim.cur_st_vec_dict.items():
              # There are 2^nbqubits stateVecs, but most do not have an associated array.
              # This has to to with doing type 2 (rather than type 0 or type 1) measurements.
              if stateVec.arr is not None:
                states = stateVec.get_traditional_st_vec()
                # states contains 2^nbqubits (=256) elements, corresponding
                # to all the states that we can have in superposition.
                for stateIdx in range(len(states)):
                  if np.absolute(states[stateIdx]) > 0.99:
                    oneState = True
                    # This is our final state, check if our original bit has been corrected
                    stateBinary = np.binary_repr(stateIdx, width=nbqubits)
                    if stateBinary[nbqubits - 1] == str(inputValue):
                      print("Error correction worked. Test succesful.")
                    else:
                      print("Error correction wrong. State = " + stateBinary)
            if not oneState:
              print("Error correction gave unexpected outcome: result is superposition of states.")

testErrorCorrection()