from abc import ABCMeta, abstractmethod

class BeatDetection(metaclass=ABCMeta):
    
    @abstractmethod
    def checkBeat(self):
        pass
