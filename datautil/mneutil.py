import sys
import time
import json
import struct
import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from mne.decoding import CSP

import mne
from mne.channels import read_layout


CNT_CHANNELS = 4


if len(sys.argv) == 1:
    print("Usage: %s <session_name>" % sys.argv[0])
    raise SystemExit(0)


session_id = sys.argv[1].replace(".raw", "").replace(".json", "").replace("data/", "")

markers = []
markers_filename = "data/" + session_id + ".json"
data_filename = "data/" + session_id + ".raw"


all_data = []
with open(data_filename, "rb") as f:
    while True:
        block = f.read(8 * CNT_CHANNELS)
        if not block:
            break
        all_data.append(struct.unpack("<" + "d" * CNT_CHANNELS, block))
all_data = np.array(list(zip(*all_data)))

all_data /= 1000000  # uV to V


ch_types = ["eeg"] * CNT_CHANNELS
ch_names = BoardShim.get_eeg_names(BoardIds.SYNTHETIC_BOARD)[:CNT_CHANNELS]
sfreq = BoardShim.get_sampling_rate(BoardIds.SYNTHETIC_BOARD)

info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
raw = mne.io.RawArray(all_data, info)

onset = []
duration = []
description = []
with open(markers_filename) as f:
    prev_marker = None
    for marker in json.loads(f.read()):
        onset.append(marker["start"] / sfreq)
        duration.append((marker["end"] - marker["start"]) / sfreq)
        description.append(marker["key"])

raw.set_annotations(mne.Annotations(onset=onset, duration=duration, description=description))

raw.set_montage(mne.channels.make_standard_montage("standard_alphabetic"))

events_from_annot, event_dict = mne.events_from_annotations(raw, event_id=lambda s: int(s))
epochs = mne.Epochs(raw, events_from_annot)
epochs.drop_bad()

csp = CSP(n_components=4, reg=None, log=True, norm_trace=False)
csp.fit_transform(epochs.get_data(), epochs.events[:, -1])
csp.plot_patterns(epochs.info, ch_type="eeg", units="Patterns (AU)", size=1.5).show()

plt.show()

# for event_type in set(description):
#     evoked = epochs[event_type].average()
#     evoked.plot()

# raw.plot(events=events_from_annot, block=True)
# raw.plot(events=events, event_color={1: "red", 2: "blue", 3: "yellow", 4: "green", 5: "black", 6: "cyan", 7: "magenta", 8: "purple", 9: "pink", 0: "grass"}, block=True)
