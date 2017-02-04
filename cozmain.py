import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps
import time
from wocdance import WocDance

d = WocDance()

cozmo.run_program(d.dance)
