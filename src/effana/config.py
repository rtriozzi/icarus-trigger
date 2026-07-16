import numpy

EFFICIENCY_VARS_RUN2 = [
  "run", "event", "length", "energy", "energy_range", 
  "t0_TPC", "t1", "dir_y", "S5", "S10", 
  "start_hit_x", "end_hit_x", "start_hit_y", "end_hit_y", "start_hit_z", "end_hit_z", 
  "start_x", "middle_x", "end_x", "start_y", "middle_y", "end_y", "start_z", "middle_z", "end_z", 
  "mediandedx", "nhits", "my_energy", "energy_last_20cm", 
  "closest_flash_t", "closest_flash_y", "closest_flash_z", "nearest_flash_t", "nearest_flash_y", "nearest_flash_z"
]

EFFICIENCY_VARS_RUN3 = [
  "run", "event", "length", "energy", "energy_range", 
  "t0_TPC", "t1", "dir_y", "S4", "S5", "S7", "S9", "S10", 
  "start_hit_x", "end_hit_x", "start_hit_y", "end_hit_y", "start_hit_z", "end_hit_z", 
  "start_x", "middle_x", "end_x", "start_y", "middle_y", "end_y", "start_z", "middle_z", "end_z", 
  "mediandedx", "nhits", "my_energy", "energy_last_20cm", 
  "closest_flash_t", "closest_flash_y", "closest_flash_z", "nearest_flash_t", "nearest_flash_y", "nearest_flash_z"
]

EFFICIENCY_VARS = {
  'Run1': EFFICIENCY_VARS_RUN2,
  'Run2': EFFICIENCY_VARS_RUN2,
  'Run3': EFFICIENCY_VARS_RUN3,
  'Run4': EFFICIENCY_VARS_RUN3,
  'Run5': EFFICIENCY_VARS_RUN3,
}

ADDER_FACTORS = {
  'Run1' : None,
  'Run2' : None,
  'Run3' : numpy.array([1.44462279, 1.05820106, 1.04931794, 1.01317123, 1.00502513, 1.]),
  'Run4' : numpy.array([1.2857, 1, 1, 1, 1, 1]),
  'Run5' : numpy.array([1.2857, 1, 1, 1, 1, 1]),
}