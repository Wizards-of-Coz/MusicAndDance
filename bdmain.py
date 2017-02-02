import pyaudio
import wave
import time
from beatdetection.EnergyBeatDetection import EnergyBeatDetection



b = EnergyBeatDetection()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 1
WAVE_OUTPUT_FILENAME = "output.wav"

b.startStream()

for i in range(0, 20):
    detected = b.checkBeat()
    if detected:
        print("Beat detected!")
    time.sleep(0.1)

b.stopStream()
