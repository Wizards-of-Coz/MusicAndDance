import wave
import time
from beatdetection.EnergyBeatDetection import EnergyBeatDetection

RECORD_SECONDS = 3
NUM_CHECKS = 20

b = EnergyBeatDetection()
b.startStream()

CHECK_TIME = b.windowTime

for i in range(0, int(RECORD_SECONDS / CHECK_TIME)):
    detected, strength = b.checkBeat()
    if detected:
        print("Beat detected!")
        print(strength)
    time.sleep(CHECK_TIME)

b.stopStream()
