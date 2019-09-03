import math
import numpy as np


def _approxEqual(x, y, tolerance=0.00001):
    return (np.abs(x) < tolerance and np.abs(y) < tolerance) or np.abs(x-y) <= 0.5 * np.abs(x + y) * tolerance

def _isCosPlusSin(phaseDiff):
  # The phase difference should be in the form cos(phi) + i sin(phi)
  if     phaseDiff.real < -1 or phaseDiff.real > 1 \
      or phaseDiff.imag < -1 or phaseDiff.imag > 1:
    print("Error: complex component of " + str(phaseDiff) + " out of bounds")
    return False
  phiReal = math.acos(phaseDiff.real) # or -phiImag.      Range is [0, PI]
  phiImag = math.asin(phaseDiff.imag) # or PI - phiImag   Range is [-PI/2, PI/2]

  if _approxEqual((phiReal - phiImag) % math.pi, 0.0) or _approxEqual((phiReal - phiImag) % math.pi, math.pi) or \
     _approxEqual((-phiReal - phiImag) % math.pi, 0.0) or _approxEqual((-phiReal - phiImag) % math.pi, math.pi) or \
     _approxEqual((phiReal - (math.pi - phiImag)) % math.pi, 0.0) or _approxEqual((phiReal - (math.pi - phiImag)) % math.pi, 0.0) or \
     _approxEqual((-phiReal - (math.pi - phiImag)) % math.pi, 0.0) or _approxEqual((-phiReal - (math.pi - phiImag)) % math.pi, 0.0):
    return True # phaseDiffA0 not of the form cos(phi) + i sin(phi)
  else:
    print(phiReal)
    print(phiImag)
    return False

def stateForInput(th, ph):
  ampl0 = complex(math.cos(ph/2) * math.cos(th/2), math.sin(ph/2) * math.cos(th/2) * -1)
  ampl1 = complex(math.sin(ph/2) * math.sin(th/2), math.cos(ph/2) * math.sin(th/2) * -1)
  return [ampl0, ampl1]

def _clampedComponents(ampl):
  comps = [ampl.real, ampl.imag]
  for compIdx in [0, 1]:
    c = comps[compIdx]
    if c < -1.0:
      if _approxEqual(c, -1.0):
        comps[compIdx] = -1.0
      else:
        print("Error: complex amplitude magnitude too large (negative).")
        exit()
    if c > 1.0:
      if _approxEqual(c, 1.0):
        comps[compIdx] = 1.0
      else:
        print("Error: complex amplitude magnitude too large (positive).")
        exit()
  return complex(comps[0], comps[1])

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
  phaseDiff = _clampedComponents(phaseDiff)
  if not _isCosPlusSin(phaseDiff):
    print("Not e^(i*phi)")
    return False

  # Finally check that the phase difference for the other eigenstate is the same
  if    basedOnEigen == 0 and _approxEqual(psiA1 * phaseDiff, psiB1) \
     or basedOnEigen == 1 and _approxEqual(psiA0 * phaseDiff, psiB0):
    return True
  else:
    print("States not identical up to global phase difference.")
    return False