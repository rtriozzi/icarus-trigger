import numpy
import pandas
import time

from .config import BEAM_INFO, GATE_NAMES, GATE_TO_NAME

# basic loader
def LoadTriggerDatabase(
  PATH : str
):

  TrigDB = pandas.read_pickle(PATH)
  RunList = sorted(TrigDB.run_number.unique())
  print(f"[LoadTriggerDatabase] Loaded {len(TrigDB)} triggers in {len(RunList)} runs"
        f" between {TrigDB.run_number.iloc[0]} ({time.ctime(TrigDB.beam_timestamp.iloc[0]/1e9)})"
        f" and {TrigDB.run_number.iloc[-1]} ({time.ctime(TrigDB.beam_timestamp.iloc[-1]/1e9)})."
  )

  return TrigDB

# process trigger database
def ProcessTriggerDatabase(
  df : pandas.DataFrame,
  debug : bool = False,
):

  # run-by-run dataframe
  RunInfo = df.groupby('run_number').agg(
      startTimeStamp=pandas.NamedAgg('beam_timestamp', 'min'),
      endTimeStamp=pandas.NamedAgg('beam_timestamp', 'max'),
      events=pandas.NamedAgg('beam_timestamp', 'size'),
  )
  RunInfo['duration'] = (RunInfo.endTimeStamp - RunInfo.startTimeStamp) / 1e9

  # trigger type -> column-name suffix: 0 is light-based (no suffix, kept as-is
  # for backward compatibility with existing column names), 1 is minimum bias
  TriggerTypeSuffix = { 0: '', 1: '_minbias' }

  # add a column for each gate type and trigger type (`<gate type><suffix>_events`)
  # with the number of events collected for that gate type and trigger type
  GateFrames = [ RunInfo ]
  for trigger_type, suffix in TriggerTypeSuffix.items():
      triggerData = df[df.trigger_type == trigger_type]
      GateFrames += [
          gateData.groupby('run_number').size().to_frame(GATE_TO_NAME[gate_type] + suffix + '_events')
          for gate_type, gateData in triggerData.groupby('gate_type')
      ]

  RunStats = (
      pandas.concat(GateFrames, axis='columns')
      .fillna(0).astype(int) # some runs don't have any event in a certain gate/trigger type
      .reset_index() # `run_number` back to a normal column
  )

  # also add the excess of beam-induced events, for each trigger type
  SignalBeams = [ beamName for beamName, beamInfo in BEAM_INFO.items() if beamInfo['hasSignal'] and (df.gate_type == beamInfo['sourceIndex']).any() ]
  for suffix in TriggerTypeSuffix.values():
      for beamName in SignalBeams:
          onCol, offCol = beamName + suffix + '_events', beamName + 'offbeam' + suffix + '_events'
          if onCol in RunStats and offCol in RunStats:
              RunStats[beamName + '_excess' + suffix + '_events'] = RunStats[onCol] - RunStats[offCol]

  # map gate type index to beam (BNB or NuMI)
  GateToBeamMap = numpy.zeros(max(info['sourceIndex'] for info in BEAM_INFO.values()) + 1, dtype=int)
  for info in BEAM_INFO.values(): GateToBeamMap[info['sourceIndex']] = BEAM_INFO[info['beamName']]['sourceIndex']

  # now add average event rates, for each trigger type
  AvailableGates = sorted(df.gate_type.unique().astype(int))
  AvailableBeams = sorted(numpy.unique(GateToBeamMap[df.gate_type]).astype(int))
  if debug:
    print(f"[ProcessTriggerDatabase] Data has {len(AvailableGates)} gates:", ", ".join(map(GATE_TO_NAME.__getitem__, AvailableGates)))
    print(f"[ProcessTriggerDatabase] Data has {len(AvailableBeams)} beams:", ", ".join(map(GATE_TO_NAME.__getitem__, AvailableBeams)))

  for suffix in TriggerTypeSuffix.values():
      streamNames = [ GATE_TO_NAME[name] + suffix for name in AvailableGates ] + [ name + '_excess' + suffix for name in SignalBeams ]
      for streamName in streamNames:
          try:
              RunStats[streamName + '_rate'] = (RunStats[streamName + '_events'] - 1) / RunStats.duration
              RunStats[streamName + '_rate_error'] = numpy.sqrt(RunStats[streamName + '_events']) / RunStats.duration
          except KeyError:
              print('[ProcessTriggerDatabase] Cathced a `KeyError` in', streamName)
              print('[ProcessTriggerDatabase] There is no `_rate` here, and maybe this was intended (e.g., for `calibration`.)')

  # also add date-wise run timestamps
  RunStats['startTimeStamp_hr'] = pandas.to_datetime(RunStats['startTimeStamp']/1.e9, unit='s')

  return RunStats

# filter run-by-run df
def FilterTriggerDataframe(
  df : pandas.DataFrame,
  beam : str = 'BNB',
):
  match beam:
    case 'BNB':
      FILTER = (df.BNB_rate*1000 > 50) \
              & (df.BNB_rate*1000 < 200) \
              & (df.duration > 3600) \
              & (df.BNB_excess_rate*1000 > 20) 
    case 'NuMI':
      FILTER = (df.NuMI_rate*1000 > 50) \
              & (df.NuMI_rate*1000 < 200) \
              & (df.duration > 3600) \
              & (df.NuMI_excess_rate*1000 > 20) 
    case _:
        print('[FilterTriggerDataframe] No matching beam. Use \'BNB\' or \'NuMI\'')
  df = df[FILTER].copy()
  return df