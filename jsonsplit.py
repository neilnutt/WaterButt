import json
import time


def downloadAvailableForecastTimes():

    apikey = "50102072-d813-4fd4-89fe-fc41a40687bc"
    url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/capabilities?res=3hourly&key='+apikey

    import urllib.request
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')

    timesteps = json.loads(data)['Resource']['TimeSteps']['TS']

    return timesteps

def downloadForecastTimestep(stationNumber,timestepString):
    apikey = "50102072-d813-4fd4-89fe-fc41a40687bc"
    url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/' + str(stationNumber) + '?time='+timestepString+'&res=3hourly&key=' + apikey

    import urllib.request
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')

    parsed = json.loads(data)

    forecast = parsed['SiteRep']['DV']['Location']['Period']['Rep']

    for k in forecast:
        if k in ('D','V'):
            pass
        elif k in ('Pp','W','U'):
            forecast[k] = int(forecast[k])
        else:
            forecast[k] = float(forecast[k])

        forecast['e_rainfall'] = rainfallFromWeatherType(forecast['W'])
        forecast['timeString'] = timestepString

    return forecast


def createHourlyWeatherSeries(forecast3hrTimeStepSeries,parameter):

    hourlyWeatherSeriesFromNow = list()

    steps = len(forecast3hrTimeStepSeries)

    for i in range(0,steps):
            hrsFromNow,step in forecast3hrTimeStepSeries:
            if hoursFromNow >= i and hoursFromNow <= i+2:
                hourlyWeatherSeriesFromNow.append(forecast3hrTimeStepSeries[i][1]['e_rainfall'])
            elif hoursFromNow > i+2 and hoursFromNow < i+3:
                w = i+2-hoursFromNow
                hourlyWeatherSeriesFromNow.append(forecast3hrTimeStepSeries[i][1]['e_rainfall']*w + forecast3hrTimeStepSeries[i+1][1]['e_rainfall']*(1-w))

    return hourlyWeatherSeriesFromNow


def dateStringToTime(dataDateString):
    textList = dataDateString.replace('T', '-').replace(':', '-').replace('Z', '').split('-')
    timeList = list()
    for i in textList:
        timeList.append(int(i))
    timeList.append(0)
    timeList.append(0)
    if dataDateString.endswith('Z'):
        timeList.append(0)
    else:
        timeList.append(1)
    timeValue = time.mktime(tuple(timeList))

    return timeValue

def foreCastAge(dataDateString):
    forecastAgeHrs = (time.time() - dateStringToTime(dataDateString)) / 60.0 / 60.0

    return forecastAgeHrs

def weatherType(inputInteger):
    '''From https://www.metoffice.gov.uk/datapoint/support/documentation/code-definitions'''
    '''Returns o = weather description'''
    i = inputInteger

    if i == 0:
        o = 'Clear night'
    elif i == 1:
        o = 'Sunny day'
    elif i == 2:
        o = 'Partly cloudy(night)'
    elif i == 3:
        o = 'Partly cloudy(day)'
    elif i == 4:
        o = 'Not used'
    elif i == 5:
        o = 'Mist'
    elif i == 6:
        o = 'Fog'
    elif i == 7:
        o = 'Cloudy'
    elif i == 8:
        o = 'Overcast'
    elif i == 9:
        o = 'Light rain shower(night)'
    elif i == 10:
        o = 'Light rain shower(day)'
    elif i == 11:
        o = 'Drizzle'
    elif i == 12:
        o = 'Light rain'
    elif i == 13:
        o = 'Heavy rain shower(night)'
    elif i == 14:
        o = 'Heavy rain shower(day)'
    elif i == 15:
        o = 'Heavy rain'
    elif i == 16:
        o = 'Sleet shower(night)'
    elif i == 17:
        o = 'Sleet shower(day)'
    elif i == 18:
        o = 'Sleet'
    elif i == 19:
        o = 'Hail shower(night)'
    elif i == 20:
        o = 'Hail shower(day)'
    elif i == 21:
        o = 'Hail'
    elif i == 22:
        o = 'Light snow shower(night)'
    elif i == 23:
        o = 'Light snow shower(day)'
    elif i == 24:
        o = 'Light snow'
    elif i == 25:
        o = 'Heavy snow shower(night)'
    elif i == 26:
        o = 'Heavy snow shower(day)'
    elif i == 27:
        o = 'Heavy snow'
    elif i == 28:
        o = 'Thunder shower(night)'
    elif i == 29:
        o = 'Thunder shower(day)'
    elif i == 30:
        o = 'Thunder'
    else:
        o = 'Not available'
    return o

def rainfallFromWeatherType(inputInteger):
    '''From https://www.metoffice.gov.uk/datapoint/support/documentation/code-definitions'''
    '''Returns guessed hourly rainfall depth in mm'''
    i = inputInteger

    if i == 0:
        #o = 'Clear night'
        d = 0.0
    elif i == 1:
        #o = 'Sunny day'
        d = 0.0
    elif i == 2:
        #o = 'Partly cloudy(night)'
        d = 0.0
    elif i == 3:
        #o = 'Partly cloudy(day)'
        d = 0.0
    elif i == 4:
        #o = 'Not used'
        d = 0.0
    elif i == 5:
        #o = 'Mist'
        d = 0.01
    elif i == 6:
        #o = 'Fog'
        d = 0.01
    elif i == 7:
        #o = 'Cloudy'
        d = 0.01
    elif i == 8:
        #o = 'Overcast'
        d = 0.01
    elif i == 9:
        #o = 'Light rain shower(night)'
        d = 0.1
    elif i == 10:
        #o = 'Light rain shower(day)'
        d = 0.1
    elif i == 11:
        #o = 'Drizzle'
        d = 0.2
    elif i == 12:
        #o = 'Light rain'
        d = 0.2
    elif i == 13:
        #o = 'Heavy rain shower(night)'
        d = 0.5
    elif i == 14:
        #o = 'Heavy rain shower(day)'
        d = 0.5
    elif i == 15:
        #o = 'Heavy rain'
        d = 1.0
    elif i == 16:
        #o = 'Sleet shower(night)'
        d = 0.2
    elif i == 17:
        #o = 'Sleet shower(day)'
        d = 0.2
    elif i == 18:
        #o = 'Sleet'
        d = 0.5
    elif i == 19:
        o = 'Hail shower(night)'
        d = 0.2
    elif i == 20:
        #o = 'Hail shower(day)'
        d = 0.2
    elif i == 21:
        #o = 'Hail'
        d = 1.0
    elif i == 22:
        #o = 'Light snow shower(night)'
        d = 0.1
    elif i == 23:
        o = 'Light snow shower(day)'
        d = 0.1
    elif i == 24:
        o = 'Light snow'
        d = 0.2
    elif i == 25:
        #o = 'Heavy snow shower(night)'
        d = 0.5
    elif i == 26:
        #o = 'Heavy snow shower(day)'
        d = 0.5
    elif i == 27:
        #o = 'Heavy snow'
        d = 1.0
    elif i == 28:
        #o = 'Thunder shower(night)'
        d = 1.0
    elif i == 29:
        #o = 'Thunder shower(day)'
        d = 1.0
    elif i == 30:
        #o = 'Thunder'
        d = 1.0
    else:
        #o = 'Not available'
        d = 0.0

    return d

if __name__ == '__main__':
    timestepsListofStrings = downloadAvailableForecastTimes()

    forecast = list()
    for timestepString in timestepsListofStrings:
        hoursFromNow = (dateStringToTime(timestepString)-time.time())/ 60.0/60.0
        if hoursFromNow > -3.0:
            forecast.append([hoursFromNow,downloadForecastTimestep('350187', timestepString)])
        else:
            pass

    #download3hrForecast('350187')
    #processed3hrForecast = process3hrForecast('3hrForecast.json')
    #rainfallHourlySeriesFromNow = createHourlyWeatherSeries(processed3hrForecast['forecastRainfall'])