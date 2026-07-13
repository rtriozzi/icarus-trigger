# `icarus-trigger`

A set of tools developed over the years to investigate the ICARUS trigger performance.

### Setup on CNAF and FNAL machines

Instructions work well at FNAL and CNAF machines, and rely on a SL7 container being available.
First, setup the ICARUS products, and an icaruscode tag:
```
source /cvmfs/icarus.opensciencegrid.org/products/icarus/setup_icarus.sh
setup icaruscode v09_89_01 -q e26:prof
```
which is what I relied on for the inaugural ICARUS trigger paper, recently [published on JINST]([url](https://iopscience.iop.org/article/10.1088/1748-0221/20/10/P10044)).
Then, create a Python virutal environment,
```
python -m venv env
source env/bin/activate
# use `pip` for installing stuff and for $$profit$$
# `deactivate` when you want to run away
```
Install the dependencies needed to run a Jupyter notebook (there are multiple online resources for that).
To run a remote notebook:
```
jupyter notebook --no-browser
# open the link on a web browser
```
If you're running the notebook on a FNAL machine, forward it to your local machine: to do this, `ssh` into the FNAL GPVM with `-L <port>:localhost:<port>`, where `<port>` is the port that the notebook opens with (e.g., `8888`).
