import numpy

HW_MISCONFIG_FACTOR = [0.11, 0.055, 0.047, 0.008, 0.002, 0.]

def AddSystematicUncertainty(
  Efficiency,
  EfficiencyError,
  TRIGGER_IDX : int = 0, # what is the PMT-Mj level you're interested in
  APPLY_MISCONFIG : bool = True,
):
  
  print(f'[AddSystematicUncertainty] Starting efficiency: f{Efficiency[TRIGGER_IDX]}')

  # get statistical error
  stat_low, stat_hi = EfficiencyError[TRIGGER_IDX].T
  stat_low, stat_hi

  print(f'[AddSystematicUncertainty] Overall stat: f{stat_low}, f{stat_hi}')

  # scale efficiency down from HW misconfiguration
  if APPLY_MISCONFIG:
    reduction = numpy.multiply(
        HW_MISCONFIG_FACTOR,
        Efficiency[TRIGGER_IDX]
    )
    EfficiencySysts = Efficiency[0] - reduction

    # the uncertainty is half of this scaling
    syst_low_emu = reduction / 2
    syst_hi_emu = reduction / 2

    print(f'[AddSystematicUncertainty] Applying mis-config: f{EfficiencySysts}, f{syst_low_emu}, f{syst_hi_emu}')
  else:
    EfficiencySysts = Efficiency[0]
    syst_low_emu = 0.
    syst_hi_emu = 0.
    
  # split trakcs: 
  # 11% lower uncertainty below 200 MeV
  # 1% lower uncertainty between 200 and 300 MeV
  syst_low_split = numpy.multiply(
      [0.11, 0.01, 0., 0., 0., 0.],
      EfficiencySysts
  )
  syst_hi_split = numpy.zeros(len(EfficiencySysts))
  syst_low_split, syst_hi_split
  
  print(f'[AddSystematicUncertainty] Applying track breaking: f{EfficiencySysts}, f{syst_low_split}, f{syst_hi_split}')

  # overall systematic error
  syst_low = numpy.sqrt(pow(syst_low_emu, 2) + pow(syst_low_split, 2))
  syst_hi = numpy.sqrt(pow(syst_hi_emu, 2) + pow(syst_hi_split, 2))

  print(f'[AddSystematicUncertainty] Overall syst: f{syst_low}, f{syst_hi}')

  # both
  EfficiencyError = [numpy.sqrt(pow(stat_low, 2) + pow(syst_low, 2)), numpy.sqrt(pow(stat_hi, 2) + pow(syst_hi, 2))]

  print(f'[AddSystematicUncertainty] Final error: f{EfficiencyError}')

  return EfficiencySysts, EfficiencyError