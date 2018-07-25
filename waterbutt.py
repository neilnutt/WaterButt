import machine
import json
import time
from hcsr04 import HCSR04
import ntptime
from umqtt.simple import MQTTClient
import ubinascii
import network
import bme280

PARAMETERS = {}

'''
ap_if = network.WLAN(network.AP_IF)
sta_if = network.WLAN(network.STA_IF)

print('Access point:')
print('Active ', ap_if.active(0))
print('ipconfig: ',ap_if.ifconfig())
print('')
print('Station:')
print('Active ', sta_if.active())
print('Is connected: ', sta_if.isconnected())
print('ipconfig: ', sta_if.ifconfig())
'''


def test():
    temp,pressure = measure_temp_pressure()
    print(temp,pressure)


    dist = measure_distance(temp)
    print(dist)

    if temp is None:
        exit()
    if dist is None:
        exit()

def initialise():
    global PARAMETERS
    print('Initialising')

    if isfile('parameters.json'):
        f = open('parameters.json','r')
        PARAMETERS = json.load(f)
        f.close()
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
    msg = msg.lower()
    if msg.startswith('emptydist'):
        PARAMETERS['minWL_mm'] = float(msg.split('=')[1])
    elif msg.startswith('fulldist'):
        PARAMETERS['maxWL_mm'] = float(msg.split('=')[1])
    elif msg.startswith('wbarea'):
        PARAMETERS['WBArea_sqm'] = float(msg.split('=')[1])
    elif msg.startswith('roofarea'):
        PARAMETERS['roofAreaDrained_sqm'] = float(msg.split('=')[1])
    elif msg.startswith('floodwarning'):
        PARAMETERS['floodwarning'] = float(msg.split('=')[1])
    f = open('parameters.json','w')
    f.write(json.dumps(PARAMETERS))
    f.close()

def measure_temp_pressure():
    i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
    bme = bme280.BME280(i2c=i2c)

    def do():
        response = bme.read_compensated_data()
        temp_100ths = response[0]
        pressure_32bit = response[1]
        temperature = temp_100ths/100.0
        pressure = pressure_32bit/256.0/100.0

        return temperature,pressure

    temperature, pressure = do()
    if pressure < 900:
        #Do it again as the first reading always seems to be a bit dodge
        time.sleep(1)
        temperature, pressure = do()

    return temperature,pressure

def measure_distance(temperature = 20, samples = 41):
    sensor = HCSR04(trigger_pin=3, echo_pin=12)
    distances = list()
    for i in range(0,samples-1):
        reading = sensor.distance_cm(temperature)*10.0
        if reading is not None and reading > 0.0:
            distances.append(reading)
            time.sleep(0.15)

    distances.sort()
    if len(distances) == 0:
        distance = None
    else:
        mean_distance_mm = sum(distances)/len(distances)
        median_distance_mm = distances[int((samples-1)/2)]
        ##print(min(distances),mean_distance_mm,median_distance_mm,max(distances))
        distance = median_distance_mm

    if len(distances) < 9:
        q1 = None
        q3 = None
    else:
        q1 = distances[int(samples/4)]
        q3 = distances[int(3* samples / 4)]

    return distance,q1,q3


def routine():
    global PARAMETERS
    PARAMETERS = initialise()

    status = dict()
    status['minWL_mm'] = PARAMETERS['minWL_mm']
    status['maxWL_mm'] = PARAMETERS['maxWL_mm']

    ip = findIP(PARAMETERS['adafruit_url'], PARAMETERS['adafruit_port'])

    c = MQTTClient(client_id=PARAMETERS['uid'], server=ip, port=PARAMETERS['adafruit_port'], user=PARAMETERS['adafruit_user'],password=PARAMETERS['adafruit_key'])
    c.set_callback(sub_cb)
    c.connect()
    #c.subscribe(b"neilnutt/feeds/emptydistmm")
    #c.subscribe(b"neilnutt/feeds/fulldistmm")
    #c.subscribe(b"neilnutt/feeds/wbareasqm")
    #c.subscribe(b"neilnutt/feeds/roofareasqm")
    c.subscribe(b"neilnutt/feeds/message")

    try:
        ntptime.settime()
    except:
        pass

    dump = machine.Pin(4, machine.Pin.OUT)
    dump.off()

    obs_rain_mm = list()
    obs_discharge_mm = list()

    for i in range(0, 14):
        obs_rain_mm.append(0.0)
        obs_discharge_mm.append(0.0)

    start_time_min = time.localtime()[4]
    print(time.localtime())

    accepted_dist,q1,q3 = measure_distance()
    c.publish(topic="neilnutt/feeds/currentwlmm", msg=str(accepted_dist))

    while True:
        c.check_msg()

#        status['WBArea_sqm'] = PARAMETERS['WBArea_sqm']
#        status['roofAreaDrained_sqm'] = PARAMETERS['roofAreaDrained_sqm']
#        status['maxWL_mm'] = PARAMETERS['maxWL_mm']
#        status['minWL_mm'] = PARAMETERS['minWL_mm']

        '''Work out what inflow is going into the waterbutt'''
        try:
            ntptime.settime()
        except:
            print('Time not updated')
            c.publish(topic="neilnutt/feeds/log", msg='Time not updated')
        start_time_s = time.time()

        #dist_before = measure_distance()
        #c.publish(topic="neilnutt/feeds/currentwlmm", msg=str(dist_before))

        percentagefull = 100* ((PARAMETERS['minWL_mm'] - PARAMETERS['maxWL_mm']) - (accepted_dist - PARAMETERS['maxWL_mm']) ) /(PARAMETERS['minWL_mm'] - PARAMETERS['maxWL_mm'])
        c.publish(topic="neilnutt/feeds/percentagefull", msg=str(percentagefull))

        temperature,pressure = measure_temp_pressure()
        c.publish(topic="neilnutt/feeds/temperature", msg=str(temperature))
        c.publish(topic="neilnutt/feeds/pressure", msg=str(pressure))
#        c.publish(topic="neilnutt/feeds/status", msg=str(json.dumps(status)))

        wait = 40
        additionalwait = wait + start_time_s - time.time()
        time.sleep(additionalwait)

        median,q1,q3 = measure_distance(temperature)

        tolerance = 0.5
        if accepted_dist + tolerance > median and accepted_dist > q3:
            old_accepted_dist = accepted_dist
            accepted_dist = median
        elif accepted_dist - tolerance < median and accepted_dist < q1:
            old_accepted_dist = accepted_dist
            accepted_dist = median
        else:
            old_accepted_dist =  accepted_dist
        c.publish(topic="neilnutt/feeds/currentwlmm", msg=str(accepted_dist))

        if old_accepted_dist < accepted_dist:
            '''Rain has gone into the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append((accepted_dist-old_accepted_dist) * (PARAMETERS['WBArea_sqm']/PARAMETERS['roofAreaDrained_sqm']))
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append(0.0)
        elif old_accepted_dist > accepted_dist:
            '''Water has been taken out of the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append(0.0)
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append((old_accepted_dist - accepted_dist) * (PARAMETERS['WBArea_sqm']/PARAMETERS['roofAreaDrained_sqm']))
        else:
            '''Water has been taken out of the butt'''
            obs_rain_mm.pop(0)
            obs_rain_mm.append(0.0)
            obs_discharge_mm.pop(0)
            obs_discharge_mm.append(0.0)

        c.publish(topic="neilnutt/feeds/obsrainmm", msg=str(obs_rain_mm[-1]))
        c.publish(topic="neilnutt/feeds/obsdischargemm", msg=str(obs_discharge_mm[-1]))

        #print(str(time.localtime()[2])+'-'+str(time.localtime()[1])+'-'+str(time.localtime()[0])+' '+str(time.localtime()[3])+':'+str(time.localtime()[4]),dist_before,dist_after,obs_rain_mm[-1],obs_discharge_mm[-1])

        additionalwait =  59.8 + start_time_s - time.time()
        time.sleep(additionalwait)
        while start_time_s + 60 > time.time():
            time.sleep(0.01)

routine()