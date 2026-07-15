import numpy
import pandas
import scipy

from .config import EFFICIENCY_VARS_RUN2, EFFICIENCY_VARS

def ImportData(
  RUN_SETTINGS : dict,
  cryo : str = 'west',
  run : str = 'Run2',
):
  # grab west data
  df_W = pandas.read_csv(
    RUN_SETTINGS['west'],
    names=EFFICIENCY_VARS[run],
    sep='\t', 
    index_col=False,
  )
  df_W = df_W.drop_duplicates()

  # grab east data
  df_E = pandas.read_csv(
    RUN_SETTINGS['east'],
    names=EFFICIENCY_VARS[run],
    sep='\t', 
    index_col=False,
  )
  df_E = df_E.drop_duplicates()

  match cryo:
    # just return west stuff
    case 'west':
      df = df_W
    # just return east stuff
    case 'east':
      df = df_E
    case 'both':
      df = pandas.concat(
        [df_W, df_E], 
        ignore_index=True, 
        sort=False
      )
    case _:
      print('[ImportData] Wrong cryostat there: use west, east, or both')

  # mask for the actual run (some files are overlapped)
  MASK_RUN = (df.run >= RUN_SETTINGS['start']) & (df.run <= RUN_SETTINGS['end'])
  df = df[MASK_RUN].copy()

  print(f'[ImportData] Loaded {run} data in {cryo} ({len(df)} entries)')

  return df

def ApplyOfflineSelection(
  df
):
  # t0_TPC comes from stitching across the TPC cathode
  # t1 comes from the CRT
  # flash matching uses only very loose OpFlashes

  # if the track is cathode-crossing, TPC and CRT should talk to each other
  # if the track is not cathode-crossing, whatever (we just need the CRT)
  MASK_TPC_CRT = ( (df.t0_TPC > -8.e3) & (numpy.abs(df.t0_TPC - df.t1) < 10) ) | (df.t0_TPC < -8e3)
  
  # loose flash matching
  MASK_PMT = (numpy.abs(df.middle_z - df.closest_flash_z) < 100)

  # track cleaning
  MASK_TRK = (df.mediandedx > 4) & (df.energy_last_20cm > 60)

  df = df[MASK_TPC_CRT & MASK_PMT & MASK_TRK].copy()

  print(f'[ApplyOfflineSelection] Ended up with {len(df)} entries')

  return df
  
def ComputeEfficiencyEnergy(
  triggers, 
  intervals, 
  feature
):
    
  # store efficiency information for this run
  efficiency     = []
  err_efficiency = []
  counts         = []
  
  # go through each trigger
  for trigger in triggers:

    # store efficiency information for each trigger
    efficiency_per_trigger = []
    err_efficiency_per_trigger = []
    counts_per_trigger = []

    # go through each interval
    for dx in intervals:

      # mask the trigger data with the interval
      mask         = (feature > dx[0]) & (feature < dx[1])
      triggers_cut = trigger[mask]

      # True = passed event; False = not catched
      n_passed = sum(triggers_cut)
      n_total  = len(triggers_cut)

      # compute efficiency
      eff     = n_passed / n_total
      ll, hl = scipy.stats.binomtest(n_passed, n_total).proportion_ci(confidence_level=0.682)
      err_eff = [eff-ll, hl-eff]

      # store results
      efficiency_per_trigger.append(eff)
      err_efficiency_per_trigger.append(err_eff)
      counts_per_trigger.append(n_total)
        
    efficiency.append(efficiency_per_trigger)
    err_efficiency.append(err_efficiency_per_trigger)
    counts.append(counts_per_trigger)
      
  # convert to numpy array for easier handling
  intervals      = numpy.array(intervals)
  efficiency     = numpy.array(efficiency)
  err_efficiency = numpy.array(err_efficiency)
  counts         = numpy.array(counts)

  # define bins
  centers = []
  errors_centers = []
  for dx in intervals:
    centers.append(numpy.mean(dx))
    errors_centers.append(numpy.mean(dx)-dx[0])
  centers = numpy.array(centers); errors_centers = numpy.array(errors_centers)
  
  return centers, errors_centers, efficiency, err_efficiency, counts