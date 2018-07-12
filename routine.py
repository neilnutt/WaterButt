import machine
import json
import time
from hcsr04 import HCSR04
import ntptime
from umqtt.simple import MQTTClient
import ubinascii
import network

PARAMETERS = {}

def initialise():
    global PARAMETERS
    print('Initialising')



    if isfile('parameters.json'):
        f = open('parameters.json','r')
        PARAMETERS = json.load(f)
    else:
        PARAMETERS = dict()
        PARAMETERS['adafruit_url'] ='io.adafruit.com'
        PARAMETERS['adafruit_port'] = 1883
        PARAMETERS['adafruit_key'] = b'2086220ca65348708a8a292b8b6029b3'
        PARAMETERS['adafruit_user'] = b'neilnutt'
        PARAMETERS['uid'] = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode().replace(':','')
        PARAMETERS['maxWL_mm'] = 100
        PARAMETERS['minWL_mm'] = 1100
        PARAMETERS['WBArea_sqm'] = 0.1
        PARAMETERS['roofAreaDrained_sqm'] = 10
        PARAMETERS['floodwarning'] = 0
        f = open('parameters.json','w')
        f.write(json.dumps(PARAMETERS))
        f.close()
    return PARAMETERS

def isfile(fname):
    try:
        f = open(fname, "r")
        exists = True
        f.close()
    except:
        exists = False
    return exists

def findIP(url,port):
    import socket
    ip = socket.getaddrinfo(url, port)[0][4][0]
    return ip

def sub_cb(topic, msg):
    print(('Received: ',topic, msg))
    global PARAMETERS
    if topic.endswith('emptydistmm'):
        PARAMETERS['minWL_mm'] = float(msg)
    elif topic.endswith('fulldistmm'):
        PARAMETERS['maxWL_mm'] = float(msg)
    elif topic.endswith('wbareasqm'):
        PARAMETERS['WBArea_sqm'] = float(msg)
    elif topic.endswith('roofareasqm'):
        PARAMETERS['roofAreaDrained_sqm'] = float(msg)


def measure_distance():
    sensor = HCSR04(trigger_pin=3, echo_pin=12)

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


def routine():
    global PARAMETERS
    PARAMETERS = initialise()

    ip = findIP(PARAMETERS['adafruit_url'], PARAMETERS['adafruit_port'])

    c = MQTTClient(client_id=PARAMETERS['uid'], server=ip, port=PARAMETERS['adafruit_port'], user=PARAMETERS['adafruit_user'],password=PARAMETERS['adafruit_key'])
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe(b"neilnutt/feeds/emptydistmm")
    c.subscribe(b"neilnutt/feeds/fulldistmm")
    c.subscribe(b"neilnutt/feeds/wbareasqm")
    c.subscribe(b"neilnutt/feeds/roofareasqm")

    try:
        ntptime.settime()
    except:
        pass

    dump = machine.Pin(4, machine.Pin.OUT)
    dump.off()

    obs_rain_mm = list()
    obs_discharge_mm = list()

    for i in range(0, 59):
        obs_rain_mm.append(0.0)
        obs_discharge_mm.append(0.0)

    start_time_min = time.localtime()[4]
    print(time.localtime())

    while True:
        c.check_msg()

        '''Work out what inflow is going into the waterbutt'''
        try:
            ntptime.settime()
        except:
            print('Time not updated')
        start_time_s = time.time()
        dist_before = measure_distance()
        c.publish(topic="neilnutt/feeds/currentwlmm", msg=str(dist_before))

        wlSampleWindow = 55

        while start_time_s + wlSampleWindow > time.time():
            time.sleep(0.1)
        dist_after = measure_distance()

        if dist_before < dist_after:
            '''Rain has gone into the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append((dist_after-dist_before) * (PARAMETERS['WBArea_sqm']/PARAMETERS['roofAreaDrained_sqm']) * wlSampleWindow/60)
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append(0.0)
        elif dist_before > dist_after:
            '''Water has been taken out of the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append(0.0)
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append((dist_before - dist_after) * (PARAMETERS['WBArea_sqm']/PARAMETERS['roofAreaDrained_sqm']) * wlSampleWindow/60)
        else:
            '''Water has been taken out of the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append(0.0)
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append(0.0)

        print(str(time.localtime()[2])+'-'+str(time.localtime()[1])+'-'+str(time.localtime()[0])+' '+str(time.localtime()[3])+':'+str(time.localtime()[4]),dist_before,dist_after,obs_rain_mm[-1],obs_discharge_mm[-1])

        while start_time_s + 60 > time.time():
            time.sleep(0.01)

if __name__ == '__main__':
    routine()