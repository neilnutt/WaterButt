print('Importing')
import time
from hcsr04 import HCSR04
import ntptime
import json
from urequests import get as uget

url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/3840?res=3hourly&key=50102072-d813-4fd4-89fe-fc41a40687bc'

data = uget(url)
f = open('3hrForecast.json','w')
f.write(data.text)
f.close()

f = open('3hrForecast.json')
text = f.read()
recordText = '{"DV'+text.split('DV')[-1][0:-1]
smallParse = json.loads(recordText)
f.close()

exit()

try:
    ntptime.settime()
except:
    pass

import machine
dump = machine.Pin(4,machine.Pin.OUT)
dump.off()

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


start_time_min = time.localtime()[4]
print(time.localtime())


def measure_distance():
    sensor = HCSR04(trigger_pin=3, echo_pin=5)

    distances = list()

    for i in range(0,9):
        reading = sensor.distance_cm()*10.0
        if reading is not None and reading > 0.0:
            distances.append(reading)

    if len(distances) == 0:
        distance = None
    else:
        distance_mm = sum(distances)/len(distances)

    return distance_mm

while True:
    '''Work out what inflow is going into the waterbutt'''
    try:
        ntptime.settime()
    except:
        print('Time not updated')
    start_time_s = time.time()
    dist_before = measure_distance()

    wlSampleWindow = 55

    while start_time_s + wlSampleWindow > time.time():
        time.sleep(0.1)
    dist_after = measure_distance()

    if dist_before < dist_after:
        '''Rain has gone into the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append((dist_after-dist_before) * (WBArea_sqm/roofAreaDrained_sqm) * wlSampleWindow/60)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append(0.0)
    elif dist_before > dist_after:
        '''Water has been taken out of the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append(0.0)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append((dist_before - dist_after) * (WBArea_sqm/roofAreaDrained_sqm) * wlSampleWindow/60)
    else:
        '''Water has been taken out of the butt'''
        obs_rain_mm.pop(0)
        obs_rain_mm.append(0.0)
        obs_discharge_mm.pop(0)
        obs_discharge_mm.append(0.0)

    print(str(time.localtime()[2])+'-'+str(time.localtime()[1])+'-'+str(time.localtime()[0])+' '+str(time.localtime()[3])+':'+str(time.localtime()[4]),dist_before,dist_after,obs_rain_mm[-1],obs_discharge_mm[-1])

    while start_time_s + 60 > time.time():
        time.sleep(0.01)

