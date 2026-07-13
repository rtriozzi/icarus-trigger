# Yhe analysis runs on top of the calibration NTuples
# separately for the west and east cryostats;
# it goes file-by-file, and launches the ROOT-based macro
# on each analysis file, writing on the same file the result

# you should check the electron lifetime, since we re-compute
# the dE/dx here from the dQ/dx directly in the macro - use
# the ICARUS database for reference, or ask someone :)

# the output is a text file with the selected stopping muons, their 
# properties, and the dE/dx as function of the residual range

echo "[LaunchStoppingMuonAnalysis.sh] Launching the stopping muon analysis. Please check paths, cryostat macro, and electron lifetime."

for file in /pnfs/icarus/scratch/users/rtriozzi/trigger_efficiency_run5a/ana/*/timed*.root; do
root -b -l << EOF
.L SelectStoppingMuons_WestCryo.C
SelectStoppingMuons_WestCryo("${file}", "SelectedStoppingMuons.out", "CaloRange.out", 7.17)
.q
EOF
done
