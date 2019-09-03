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

emb = CktEmbedder(3, 3)
file_prefix = 'bitflip_encode_example'
wr = SEO_writer(file_prefix, emb)
wr.write_cnot(control_bit=0, target_bit=1)
wr.write_cnot(control_bit=0, target_bit=2)
# Some errors might have been introduced here,
# in which case error correction should be done here.
wr.write_MEAS(0, 2)
wr.close_files()

state_vec = StateVec.get_standard_basis_st_vec([0, 0, 0])
sim = SEO_simulator(file_prefix, 3, state_vec)
state_vec.describe_self()