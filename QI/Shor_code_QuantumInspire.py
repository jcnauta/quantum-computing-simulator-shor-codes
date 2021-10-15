# Shor-code implementation for Qiskit

from quantuminspire.api import QuantumInspireAPI
from getpass import getpass

import numpy as np 
import itertools

nbqubits = 9

def PrepareState(inputValue):
  return '''
    RX q[0], {0}
    RZ q[0], {1}
    '''.format(inputValue['theta'], inputValue['phi'])

def BitFlipEncode(indices):
  return '''CNOT q[{0}], q[{1}]
  CNOT q[{0}], q[{2}]
  '''.format(*indices)

def PhaseFlipEncode(indices):
  return BitFlipEncode(indices) + '''H q[{0}]
  H q[{1}]
  H q[{2}]
  '''.format(*indices)

def ErrorIntroduction(bitErrors):
  state = ''''''
  for err in bitErrors:
    state += '''X q[{0}]
    Z q[{0}]
    '''.format(err)
  return state
  
def BitFlipDecode(indices):
  return '''CNOT q[{0}], q[{1}]
  CNOT q[{0}], q[{2}]
  Toffoli q[{2}], q[{1}], q[{0}]
  '''.format(*indices)
  
def PhaseFlipDecode(indices):
  return '''H q[{0}]
  H q[{1}]
  H q[{2}]
  '''.format(*indices) + BitFlipDecode(indices)
  
def createProgram(inputValue, errorIdxs):
  QASM = '''version 1.0\nqubits {0}
  '''.format(nbqubits)
    
  QASM += PrepareState(inputValue)
  
  QASM += PhaseFlipEncode([0,3,6])
  QASM += BitFlipEncode([0,1,2])
  QASM += BitFlipEncode([3,4,5])
  QASM += BitFlipEncode([6,7,8])
  
  QASM += ErrorIntroduction(errorIdxs)
  
  QASM += BitFlipDecode([6,7,8])
  QASM += BitFlipDecode([3,4,5])
  QASM += BitFlipDecode([0,1,2])
  QASM += PhaseFlipDecode([0,3,6])
  
  return QASM
 
def _stateForInput(th, ph):
  ampl0 = complex(np.cos(ph/2) * np.cos(th/2), np.sin(ph/2) * np.cos(th/2) * -1)
  ampl1 = complex(np.sin(ph/2) * np.sin(th/2), np.cos(ph/2) * np.sin(th/2) * -1)
  return [ampl0, ampl1]
 
def testErrorCorrection():
  server_url = r'https://api.quantum-inspire.com'
  
  print('Enter mail address')
  email = input()

  print('Enter password')
  password = getpass()
  auth = (email, password)
  
  qi = QuantumInspireAPI(server_url, auth)
  backend = qi.get_backend_type_by_name('QX single-node simulator')
  
  inputValues = [{'theta': 0, 'phi': 0}, #|0>
                 {'theta': np.pi, 'phi': np.pi}, #|1>
                 {'theta': np.pi/2, 'phi': np.pi/2} #|+>
                ]
  
  for inputValue in inputValues:
    print("Using input value " + str(inputValue))
    allErrorIdxs = []
    for nrOfErrors in range(2):
      allErrorIdxs += itertools.combinations(range(nbqubits), nrOfErrors)
    # iterate over all possible combinations of errors
    
    for errorIdxs in allErrorIdxs:
      inputStateComplex = _stateForInput(inputValue['theta'], inputValue['phi'])
    
      print("Introducing errors, indices " + str(errorIdxs))
      QASM = createProgram(inputValue, errorIdxs)
      
      prob_0 = 0
      prob_1 = 0
      
      if 1: # Wavefunction
        result = qi.execute_qasm(QASM, backend_type=backend, number_of_shots=1)
      else: # Do measurements
        result = qi.execute_qasm(QASM, backend_type=backend, number_of_shots=10)
      
      result = result['histogram']  
      for key, value in zip(result.keys(), result.values()):
        if (int(key) % 2) == 0: #Number is odd
            prob_0 += value
        else:
            prob_1 += value
            
      if abs(prob_0 - abs(inputStateComplex[0])**2) < 0.0001 and abs(prob_1 - abs(inputStateComplex[1])**2) < 0.0001:
        print("Error correction works")
      else:
        print("Error correction fails")
        
res = testErrorCorrection()
