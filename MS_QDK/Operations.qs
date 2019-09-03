namespace Quantum.ShorCode
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Convert;
    
    operation PrepareState(qubits: Qubit[], initial: Double[]): Unit{
      Rx((initial[0], qubits[0]));
      Rz((initial[1], qubits[0]));
    }

    operation BitFlipEncode(qubits: Qubit[], idxs: Int[]): Unit{
      Controlled X([qubits[idxs[0]]], qubits[idxs[1]]);
      Controlled X([qubits[idxs[0]]], qubits[idxs[2]]);
    }

    operation PhaseFlipEncode(qubits: Qubit[], idxs: Int[]): Unit{
      BitFlipEncode(qubits, idxs);
      for (idx in idxs){
        H(qubits[idx]);
      }
    }

    operation ErrorIntroduction(qubits: Qubit[], idxs: Int[]): Unit{
      for (idx in idxs){
        X(qubits[idx]);
        Z(qubits[idx]);
      }
    }

    operation BitFlipDecode(qubits: Qubit[], idxs: Int[]): Unit{
      Controlled X([qubits[idxs[0]]], qubits[idxs[1]]);
      Controlled X([qubits[idxs[0]]], qubits[idxs[2]]);
      Controlled X([qubits[idxs[2]], qubits[idxs[1]]], qubits[idxs[0]]);
    }

    operation PhaseFlipDecode(qubits: Qubit[], idxs: Int[]): Unit{
      for (idx in idxs){
        H(qubits[idx]);
      }
      BitFlipDecode(qubits, idxs);
    }

    // This function is written to accept an arbitrary input state (theta and phi angles)
    // but the comparison at the end assumes a pure |0> or |1> state.
    operation TestShorCode(input_theta_and_phi: Double[], error_idxs: Int[]): Bool{
        using (qubits = Qubit[9]){
          PrepareState(qubits, input_theta_and_phi);
          PhaseFlipEncode(qubits, [0, 3, 6]);
          BitFlipEncode(qubits, [0, 1, 2]);
          BitFlipEncode(qubits, [3, 4, 5]);
          BitFlipEncode(qubits, [6, 7, 8]);
          ErrorIntroduction(qubits, error_idxs);
          BitFlipDecode(qubits, [6, 7, 8]);
          BitFlipDecode(qubits, [3, 4, 5]);
          BitFlipDecode(qubits, [0, 1, 2]);
          PhaseFlipDecode(qubits, [0, 3, 6]);
          // The only way to check the full state is using the DumpMachine function.
          // This however outputs the state in plain text which we would have to
          // manually convert into a data structure for meaningful comparison.
          
          // DumpMachine(());
          
          // We could also check the state of a single qubit, but this assumes that
          // the qubit is not entangled.

          // AssertQubitIsInStateWithinTolerance((Complex(0., 0.), Complex(0., 1.)), qubits[0], 0.01);

          let outcome = M(qubits[0]);
          mutable matching = false;
          if ((IsResultZero(outcome) and AbsD(input_theta_and_phi[0]) < 0.001) or
              (IsResultOne(outcome) and AbsD(input_theta_and_phi[0] - PI()) < 0.001)) {
              set matching = true;
          }
          ResetAll(qubits);
          return matching;
        }
    }
}
