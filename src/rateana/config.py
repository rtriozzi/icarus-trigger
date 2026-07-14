# high-level settings for each stream
BEAM_INFO = {
    'BNB':         dict(name='BNB',         beamName='BNB',         color=('C1', 1), sourceIndex=1, reference={ 'spill': 1.6, 'rate': 4.0,    'POT/spill': 3.5e12 }, veto=4.0, hasSignal=True,  scale=1.0, lw=1.5),
    'NuMI':        dict(name='NuMI',        beamName='NuMI',        color=('C1', 1), sourceIndex=2, reference={ 'spill': 9.5, 'rate': 0.9375, 'POT/spill': 4.0e13 }, veto=4.0, hasSignal=True,  scale=1.0, lw=1.5),
    'BNBoffbeam':  dict(name='BNBoffbeam',  beamName='BNB',         color=('C0', 1), sourceIndex=3, reference={ 'spill': 1.6, 'rate': 4.0,    'POT/spill': 3.5e12 }, veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
    'NuMIoffbeam': dict(name='NuMIoffbeam', beamName='NuMI',        color=('C0', 1), sourceIndex=4, reference={ 'spill': 9.5, 'rate': 0.9375, 'POT/spill': 4.0e13 }, veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
    'calibration': dict(name='calibration', beamName='calibration', color=('mediumpurple', 0.4), sourceIndex=5, reference={ 'spill': 1.6, 'rate': 1.00,   'POT/spill': 0.0  },   veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
}

GATE_NAMES = [ 'BNB', 'BNBoffbeam', 'NuMI', 'NuMIoffbeam', 'calibration' ] # here for the order

# give a proper name to each stream
GATE_TO_NAME = [ None ] * (len(BEAM_INFO) + 1)
for beamInfo in BEAM_INFO.values(): GATE_TO_NAME[beamInfo['sourceIndex']] = beamInfo['name']

RUN_PERIODS = {
    'Run1':       dict(tag='Run1', name='ICARUS Run1', firstRun= 8460,  lastRun= 8554, prescale=dict(BNB=200, NuMI=60, BNBoffbeam=20, NuMIoffbeam=20), color='teal'       ),
    'Run2':       dict(tag='Run2', name='ICARUS Run2', firstRun= 9301,  lastRun=10097, prescale=dict(BNB=200, NuMI=60, BNBoffbeam=20, NuMIoffbeam=20), color='orange'     ),
    'Run3':       dict(tag='Run3', name='ICARUS Run3', firstRun=11806,  lastRun=12037, prescale=dict(BNB= 40, NuMI=30, BNBoffbeam=20, NuMIoffbeam=20), color='forestgreen'),
    'Run4':       dict(tag='Run4', name='ICARUS Run4', firstRun=12962,  lastRun=13272, prescale=dict(BNB= 40, NuMI=30, BNBoffbeam=20, NuMIoffbeam=20), color='purple'     ),
    'Run5':       dict(tag='Run5', name='ICARUS Run5', firstRun=13758,  lastRun=99999, prescale=dict(BNB= 40, NuMI=30, BNBoffbeam=20, NuMIoffbeam=20), color='navy'    ),
    # "preparation" included changes in trigger (adders), beam gate delays, minimum bias prescale
    'Run3prep':   dict(tag='Run3prep',   name='ICARUS Run3 preparation (to 2024-03-30)', firstRun=11806, lastRun=11834, prescale=dict(BNB=200, NuMI=60, BNBoffbeam=20, NuMIoffbeam=20)), # before the change of beam gate delays
    'Run3stable': dict(tag='Run3stable', name='ICARUS Run3 (2024-03-30 on)',             firstRun=11835, lastRun=12037, prescale=dict(BNB= 40, NuMI=30, BNBoffbeam=20, NuMIoffbeam=20)), # after the change of beam gate delays
}