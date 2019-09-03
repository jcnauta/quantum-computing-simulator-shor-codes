using System;

using Microsoft.Quantum.Simulation.Core;
using Microsoft.Quantum.Simulation.Simulators;

namespace Quantum.ShorCode
{
  class Driver
  {
    static void Main(string[] args)
    {
      double[][] input_values = {new double[] {0.0, 0.0},  //  |0>
                    new double[] {0.0, Math.PI * 2.0 / 3.0}, //  also |0>, phi should not matter.
                    new double[] { Math.PI, 0.0},  //  |1>
                    new double[] { Math.PI, 2.0 } };//  also |1>, phi should not matter.
                                          //new double[] {Math.PI / 2.0, 0.0},  // 1/sqrt(2) * ( |0> + |1> )
                                          //new double[] {Math.PI / 2.0, 2.0},  // Phase should not matter
                                          //new double[] {Math.PI * 2.0 / 3.0, 4.0} };  // Uneven superposition
    long[][] all_error_idxs = new long[][] {
                    new long[] { },
                    new long[] { 0 },
                    new long[] { 1 },
                    new long[] { 2 },
                    new long[] { 3 },
                    new long[] { 4 },
                    new long[] { 5 },
                    new long[] { 6 },
                    new long[] { 7 },
                    new long[] { 8 }
      };
      using (var qsim = new QuantumSimulator())
      {
        var nr_of_errors = 0;
        foreach (double[] theta_and_phi in input_values) {
          foreach (long[] error_idxs in all_error_idxs) {
            try // Try/Catch only used when working with exceptions from Diagonostics.
            {
              // Print out input values and indices.

              foreach (var input_angles in input_values)
              {
                Console.Write("Input angles: ");
                foreach (var angle in input_angles)
                {
                  Console.Write(angle.ToString() + " ");
                }
                Console.WriteLine();
              }
              Console.Write("Error introduced on qubit(s) ");
              foreach (var error_idx in error_idxs)
              {
                Console.Write(error_idx.ToString() + " ");
              }
              Console.WriteLine();
              Console.Out.Flush();
              bool matching = TestShorCode.Run(qsim, new QArray<double>(theta_and_phi), new QArray<long>(error_idxs)).Result;
              if (matching)
              {
                Console.WriteLine("Error correction succesful.");
              }
              else
              {
                nr_of_errors += 1;
                Console.WriteLine("Output state not in agreement with input!");
              }
            } catch
            {
              Console.WriteLine("Caught exception while running Shor code!");
              continue;
            }
          }
        }
        if (nr_of_errors == 0)
        {
          Console.WriteLine("All tests completed succesfully.");
        }
        else
        {
          Console.WriteLine("{0} out of {1} error corrections failed!", nr_of_errors, input_values.Length * all_error_idxs.Length);
        }
      }
    }
  }
}