echo "[DumpRunRawFiles.sh] The base path below depends on the DAQ version used for this run -- please check this with samweb before continuing."

# write a temporary list of run files using samweb -- this gives the files names
touch temp.list
samweb list-files "run_number=13906 AND data_tier raw" | grep "OffBeamMINBIAS" > temp.list

# attach the DAQ path to each file name and write to a proper list
cat temp.list | while read file
do 
    echo "/pnfs/icarus/archive/sbn/sbn_fd/data/raw/offbeamminbiascalib/v1_10_09/icarus_daq_v1_10_09/daq/00/01/39/06/${file}" >> List13906_Raw.list
done

# remove the temporary list
rm temp.list