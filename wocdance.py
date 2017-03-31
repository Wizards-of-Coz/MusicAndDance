import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps
import time
from beatdetection.EnergyBeatDetection import EnergyBeatDetection
import asyncio
import threading
import math


RECORD_SECONDS = 60
DANCE_DURATION_MIN = 0.1
DANCE_DURATION_MAX = 0.3
HEAD_SPEED = 3
LIFT_SPEED = 3
WHEEL_SPEED = 400

class WocDance:
    
    def __init__(self):
        self.b = EnergyBeatDetection()
        self.CHECK_TIME = self.b.windowTime
        self.beatDetected = False
        self.beatStrength = 0.0
        self.audioFin = False
        self.lock = threading.Lock()

    def danceMove(self, robot: cozmo.robot.Robot, speed, direction):
        robot.move_lift(speed * direction)
        robot.move_head(-speed * direction)

    def stopMove(self, robot: cozmo.robot.Robot):
        robot.stop_all_motors()
    
    async def dance(self, robot: cozmo.robot.Robot):
        t1 = threading.Thread(target=self.checkBeatThread, args=[])
        t1.start()
        
        await self.danceLoop(robot)

    def danceSync(self, robot: cozmo.robot.Robot):
        for i in range(0, int(RECORD_SECONDS / self.CHECK_TIME)):
            detected, strength = self.b.checkBeat()
            if detected:
                print("Beat detected!")
                #print(strength)
                self.danceMove(robot, 2, self.liftDirection)
                self.liftDirection *= -1
            else:
                self.stopMove(robot)
            time.sleep(self.CHECK_TIME)

    async def checkBeatAsync(self):
        self.b.startStream()
        endCount = int(RECORD_SECONDS / self.CHECK_TIME)
        i = 0
        while (i < endCount):
            i += 1
            detected, strength = self.b.checkBeat()
            if detected:
                print("Beat detected!")
                #print(strength)
                
                self.lock.acquire()
                self.beatDetected = True
                self.beatStrength = strength
                self.lock.release()
                
            await asyncio.sleep(self.CHECK_TIME)
          
        self.lock.acquire()
        self.audioFin = True
        self.lock.release()
        
        self.b.stopStream()

    def checkBeatThread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.checkBeatAsync())
    
    async def danceLoop(self, robot: cozmo.robot.Robot):
        HEAD_MOVE_THRS = self.b.ABSOLUTE_THRESHOLD
        LIFT_MOVE_THRS = 2 * HEAD_MOVE_THRS
        WHEEL_MOVE_THRS = 5 * HEAD_MOVE_THRS
        FLIP_THRS = 10 * HEAD_MOVE_THRS
        headDirection = 1
        liftDirection = 1
        wheelDirection = 1
        
        self.lock.acquire()
        danceFin = self.audioFin
        self.lock.release()

        detected = False
        strength = 0.0
        
        while (not danceFin):
            #TODO: variable time
            if detected:
                duration = self.computeDuration(strength)
                print(strength)
                print(duration)
                if duration > self.CHECK_TIME:
                    continue

                # if strength > FLIP_THRS:
                flipStrength = strength > FLIP_THRS
                headLimited = robot.head_angle.radians <= cozmo.robot.MIN_HEAD_ANGLE.radians+0.015 or robot.head_angle.radians >= cozmo.robot.MAX_HEAD_ANGLE.radians-0.015
                liftLimited = robot.lift_height.distance_mm <= cozmo.robot.MIN_LIFT_HEIGHT_MM+3.0 or robot.lift_height.distance_mm >= cozmo.robot.MAX_LIFT_HEIGHT_MM-3.0
                
                if flipStrength or headLimited:
                    headDirection *= -1

                if flipStrength or liftLimited:
                    liftDirection *= -1

                if flipStrength:
                    wheelDirection *= -1

                    
                if strength > HEAD_MOVE_THRS:
                    robot.move_head(headDirection * HEAD_SPEED)
                    
                if strength > LIFT_MOVE_THRS:
                    robot.move_lift(liftDirection * HEAD_SPEED)
                    
                if strength > WHEEL_MOVE_THRS:
                    await robot.drive_wheels(wheelDirection * WHEEL_SPEED,
                                       -wheelDirection * WHEEL_SPEED)

                await asyncio.sleep(duration)

                robot.stop_all_motors()

                await asyncio.sleep(self.CHECK_TIME - duration)
                    
                
            else:
                await asyncio.sleep(self.CHECK_TIME)
            
            self.lock.acquire()
            danceFin = self.audioFin
            detected = self.beatDetected
            self.beatDetected = False
            strength = self.beatStrength
            self.lock.release()

    def computeDuration(self, strength: float):
        # direction, duration
        # duration follows:
        # dr = a * log2(c * strength)
##        a = 0.02038
##        c = 30
##        duration = a * math.log2(30 * strength)

        # dr = a * strength + b
        a = 0.00333
        b = 0.097
        duration = a * strength + b
        duration = max(DANCE_DURATION_MIN, min(duration, DANCE_DURATION_MAX))
        return duration
