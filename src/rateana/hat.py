
import numpy
import pandas
import time

from .config import BEAM_INFO, GATE_NAMES, GATE_TO_NAME, RUN_PERIODS

BINNING = {
  'BNB': {  'range': ( 0.064*-0.5, 0.064*40.5 ), 'binWidth': 0.064, },
  'NuMI': { 'range': ( 0.256*-0.5, 0.256*42.5 ), 'binWidth': 0.064, },
}

def PlotTriggerHatPlot(
  ax, 
  db, 
  beam : str = 'BNB',
  run : str = 'Run2',
):
  # get basic info
  BeamInfo = BEAM_INFO[beam]
  RunPeriod = RUN_PERIODS[run]
  periodData = db[(db.trigger_type == 0) & db.run_number.between(RunPeriod['firstRun'], RunPeriod['lastRun'])]
  data = periodData[periodData.gate_type == BeamInfo['sourceIndex']]
  if len(data) == 0: return

  # binning
  binningInfo = BINNING[beam]
  bins = numpy.arange(binningInfo['range'][0], binningInfo['range'][1], binningInfo['binWidth']) + 0.001

  # plot
  onbeam = data.triggerFromBeamGate/1e3 - BeamInfo['veto']
  ax.hist(
    onbeam,
    bins=bins,
    histtype="step",
    color=BeamInfo['color'],
    label=f"{BeamInfo['name']} ({len(onbeam)} events)",
    linewidth=1.5
  )

  # offbeam
  OffbeamInfo = BEAM_INFO[beam + 'offbeam']
  offbeamdata = periodData[periodData.gate_type == OffbeamInfo['sourceIndex']]
  offbeam = offbeamdata.triggerFromBeamGate/1e3 - OffbeamInfo['veto']
  ax.hist(
    offbeam, 
    bins=bins,
    histtype="step",
    color=OffbeamInfo['color'],
    label=f"off-beam ({len(offbeam)} events)",
    linewidth=1.0
  )

  return ax
