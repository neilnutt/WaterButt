print('Importing')
import time
from hcsr04 import HCSR04
import ntptime

maxWL_mm = 100
minWL_mm = 1100

WBArea_sqm = 0.1
roofAreaDrained_sqm = 10

floodwarning = 0

obs_rain_mm = list()
obs_discharge_mm = list()

for i in range(0,59):
    obs_rain_mm.append(0.0)
    obs_discharge_mm.append(0.0)

ntptime.settime()
start_time_min = time.localtime()[4]
print(time.localtime())


def measure_distance():
    sensor = HCSR04(trigger_pin=3, echo_pin=4)

    distances = list()

    for i in range(0,9):
        reading = sensor.distance_cm()
        if reading is not None and reading > 0.0:
            distances.append(reading)
    distance = sum(distances)/len(distances)

    return distance


while False:
    '''Work out what inflow is going into the waterbutt'''
    ntptime.settime()
    start_time_s = time.localtime()[5]
    dist_before = measure_distance()

    print(start_time_s)


    while start_time_s < time.localtime()[5]+55:
        time.sleep(0.1)
    dist_after = measure_distance()

    if dist_before < dist_after:
        '''Rain has gone into the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append((dist_after-dist_before) * (roofAreaDrained_sqm / WBArea_sqm) * 55/60)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append(0.0)
    elif dist_before > dist_after:
        '''Water has been taken out of the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append(0.0)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append((dist_before - dist_after) * (roofAreaDrained_sqm / WBArea_sqm) * 55/60)
    else:
        '''Water has been taken out of the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append(0.0)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append(0.0)

    print(time.localtime(),dist_before,dist_after,obs_rain_mm,obs_discharge_mm)

    while start_time_s < time.localtime()[5]+60:
        time.sleep(0.01)

