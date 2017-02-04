# Author: Carsten Huang
# algorithm reference: http://mziccard.me/2015/05/28/beats-detection-algorithms-1/

from .BeatDetection import BeatDetection
import pyaudio
import threading


CHUNK = 1024
FORMAT = pyaudio.paInt16
BYTES_PER_DATUM = 2
CHANNELS = 2
RATE = 44100
WINDOW_SIZE = 16
INT16_MAX_F = 32768.0

# energy threshold test
# E > C(E) * avg(E)
# C(E) = Ca * var(E) + Cb
# Ca = -0.0000015, Cb = 1.5142857
Ca = -0.0000015
Cb = 1.5142857

class EnergyBeatDetection(BeatDetection):
    ABSOLUTE_THRESHOLD = 5e-1
    # ABSOLUTE_THRESHOLD = 1e-1
    
    beatDetected = False
    # circular buffer to store energy of current window
    energyWindow = []
    headIndex = 0
    size = 0
    avg = 0.0
    lock = threading.Lock()
    windowTime = float(CHUNK * WINDOW_SIZE) / float(RATE)
    
    def __init__(self):
        self.p = pyaudio.PyAudio()
    
    # callback
    def _collectData(self, in_data, frame_count, time_info, status):
        # compute energy of this chunk
        energy = 0.0
        for i in range(0, int(CHUNK * CHANNELS)):
            begin = i*BYTES_PER_DATUM
            num = int.from_bytes(in_data[begin : begin + BYTES_PER_DATUM],
                                 byteorder='little',
                                 signed=True)
            f = float(num) / INT16_MAX_F
            energy += (f*f)
        self.lock.acquire()
        if self.size < WINDOW_SIZE:
            # entries to fill list
            self.size += 1
            self.energyWindow.append(energy)
            self.avg += energy / float(WINDOW_SIZE)
        else:
            # list already full
            self.avg -= self.energyWindow[self.headIndex] / float(WINDOW_SIZE)
            self.avg += energy / float(WINDOW_SIZE)
            self.energyWindow[self.headIndex] = energy
            self.headIndex += 1
            if self.headIndex == WINDOW_SIZE:
                self.headIndex = 0
        self.lock.release()
        return (None, pyaudio.paContinue)

    # energy method is not real time
    # check ifany beat in window instead
    def checkBeat(self):
        # compute variance and compare
        if self.size < WINDOW_SIZE:
            return (False, 0.0)
        var = 0.0
        detected = False
        self.lock.acquire()
        for i in range(0, WINDOW_SIZE):
            diff = self.energyWindow[i] - self.avg
            var += diff * diff / float(WINDOW_SIZE)
        C = Ca * var + Cb
        threshold = C * self.avg
        strength = 0.0
        for i in range(0, WINDOW_SIZE):
            candidate = self.energyWindow[i]
            if candidate > threshold and candidate > self.ABSOLUTE_THRESHOLD:
                detected = True
                strength = candidate
                break
        self.lock.release()
        return (detected, strength)

    def startStream(self):
        try:
            self.stream = self.p.open(format=FORMAT,
                                 channels=CHANNELS,
                                 rate=RATE,
                                 input=True,
                                 frames_per_buffer=CHUNK,
                                 stream_callback=self._collectData)
        except IOError as e:
            print(e)
            self.stream.close()
        self.stream.start_stream()

    def stopStream(self):
        self.stream.stop_stream()
        self.stream.close()
