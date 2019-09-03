## QLM

To run the QLM-code, you need an account with Surfsara.
On their server, you can simply run the program with python3 <name-of-script>

To visualize the circuit, first write the .circ file:

```
import qat.core.circ as circ
circuit = Program()
...
circ.writecirc(circuit.to_circ(), "output.circ")
```

From the command line create a pdf from this:

```
qat-circprint output.circ output
```

The resulting output.pdf shows up blank for me in Microsoft Edge (no surprises), but Adobe Reader Touch correctly shows the circuit.