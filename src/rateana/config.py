# high-level settings for each stream
BEAM_INFO = {
    'BNB':         dict(name='BNB',         beamName='BNB',         color=('darkorange', 1), sourceIndex=1, reference={ 'spill': 1.6, 'rate': 4.0,    'POT/spill': 3.5e12 }, veto=4.0, hasSignal=True,  scale=1.0, lw=1.5),
    'NuMI':        dict(name='NuMI',        beamName='NuMI',        color=('darkblue', 1), sourceIndex=2, reference={ 'spill': 9.5, 'rate': 0.9375, 'POT/spill': 4.0e13 }, veto=4.0, hasSignal=True,  scale=1.0, lw=1.5),
    'BNBoffbeam':  dict(name='BNBoffbeam',  beamName='BNB',         color=('orange', 1), sourceIndex=3, reference={ 'spill': 1.6, 'rate': 4.0,    'POT/spill': 3.5e12 }, veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
    'NuMIoffbeam': dict(name='NuMIoffbeam', beamName='NuMI',        color=('blue', 1), sourceIndex=4, reference={ 'spill': 9.5, 'rate': 0.9375, 'POT/spill': 4.0e13 }, veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
    'calibration': dict(name='calibration', beamName='calibration', color=('mediumpurple', 0.4), sourceIndex=5, reference={ 'spill': 1.6, 'rate': 1.00,   'POT/spill': 0.0  },   veto=4.0, hasSignal=False, scale=1.0, lw=1.0),
}

GATE_NAMES = [ 'BNB', 'BNBoffbeam', 'NuMI', 'NuMIoffbeam', 'calibration' ] # here for the order

# give a proper name to each stream
GATE_TO_NAME = [ None ] * (len(BEAM_INFO) + 1)
for beamInfo in BEAM_INFO.values(): GATE_TO_NAME[beamInfo['sourceIndex']] = beamInfo['name']