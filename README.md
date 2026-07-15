# `icarus-trigger`

A set of tools developed over the years to investigate the ICARUS trigger performance.
- [Setup on CNAF and FNAL machines](#setup-on-cnaf-and-fnal-machines)
- [Trigger rate investigations](#trigger-rate-investigations)
- [Process data and submit jobs](#process-data-and-submit-jobs)
- [Select stopping muons with trigger emulation](#select-stopping-muons-with-trigger-emulation)
- [Trigger efficiency analysis](#trigger-efficiency-analysis)

### Setup on CNAF and FNAL machines

Instructions work well at FNAL and CNAF machines, and rely on a SL7 container being available.
First, setup the ICARUS products, and an icaruscode tag:
```
source /cvmfs/icarus.opensciencegrid.org/products/icarus/setup_icarus.sh
setup icaruscode v09_89_01 -q e26:prof
```
which is what I relied on for the inaugural ICARUS trigger paper, recently [published on JINST](https://iopscience.iop.org/article/10.1088/1748-0221/20/10/P10044).
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

### Trigger rate investigations

There is a dedicated ICARUS database to look into trigger information (rates, hat plots, ...).
Some tools developed by Gianluca Petrillo (petrillo@slac.stanford.edu) are provided here.

To download database data, first enstablish a tunnel to ifdbdaqrep01 via a GPVM.
Then, for example:
```
python3 ../scripts/TriggerDatabaseAccess.py --password=<password> --fromrun=13799 --torun=13802
```

You can analyze the resulting files with `notebooks/TriggerRates.ipynb`.

### Process data and submit jobs

Once ICARUS products are setup, you can process data (give a look at `scripts/DumpRunRawFiles.sh`). 
For reference, you can use the old-ish, but stable, `v09_89_01` icaruscode tag.
From the raw file, you can use `lar` to process data through the Stage0, Stage1, and analysis stages (minimal usage: `lar -c <config> <file>`), with the following chain:

1. `stage0_run2_icarus.fcl`;
2. `config/fcl/stage1_run2_1d_icarus_AllTrack.fcl` (preserves _all_ reconstructed tracks);
3. `config/fcl/NTuples_CRT_TrigEmu_LooseOpFlash_AllMjs.fcl` (runs trigger emulation, extracts easy-to-use ROOT TTree).

When processing a large set of files, you _really_ should get into the grid: you can use the grid configurations in `config/grid` (based on `LArBatch/project.py`).

### Select stopping muons with trigger emulation

The last processing stage outpus a set of ROOT TTrees (or, NTuples), where each entry is a reconstructed track, along with the associated TPC, CRT, PMT, and trigger information.
The two ROOT macros in `src/ntuple` can be used to select the tracks identified as "stopping muons" from each analysis NTuple, taking as input two file names (to store output information for further analysis), and the electron lifetime (expressed in ms) of the corresponding DAQ run.

Launch the analysis on a whole batch of data with `scripts/LaunchStoppingMuonAnalysis.sh`: this is currently set up to run on the west cryostat; please create a similar script for the east cryostat if you like this.
Note: launch this in the background and monitor the results (`nohup bash scripts/LaunchStoppingMuonAnalysis.sh > Ouput.out &`); you should be using `tmux` or `screen` if you're working within a SL7 container.

The output is a file where some of the stopping muon properties are stored along with the result of the trigger emulation.

### Trigger efficiency analysis

To extract trigger efficiencies (and more), the output of the analysis is all you need. Take a look at `notebooks/efficiency` and `notebooks/calorimetry`.
