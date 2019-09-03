Install cirQ using the instructions on https://cirq.readthedocs.io/en/stable/install.html
Concrete steps here:

```
conda create -n cirQ python=3.5
conda activate cirQ
python -m pip install --upgrade pip
python -m pip install numpy
sudo apt-get install libfreetype6-dev
python -m pip install cirq
```

Our program can then simply be run from the command line.
Note that other Python versions might not work, e.g. Python 3.7 did not work for us due to problems with numpy.