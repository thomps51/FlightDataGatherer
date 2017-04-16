from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException  
import time
from datetime import datetime, timedelta
import re
#import MySQLdb
import hashlib


# locally defined functions
from htmlParsing import *

# SQL tables
class PriceHistory(object):
    pass
class FlightStop(object):
    pass
class Layover(object):
    pass
class FlightInfo(object):
    pass

def check_link_exists(browser, linkText):
  try:
    browser.find_element_by_id(linkText)
  except NoSuchElementException:
    return False
  return True

def saveClassListToCSV(csvName, objects):
  print "writing " + csvName
  f = open(csvName+".csv","w") 
  
  if len(objects) > 0:
    members = [attr for attr in dir(objects[0]) if not callable(getattr(objects[0], attr)) and not attr.startswith("__")]
    columnNames=""
    for member in members:
      columnNames = columnNames + member + ","
    columnNames = columnNames[0:-1] + '\n'
    f.write(columnNames)
  else:
    print "no objects!"
  
  for obj in objects:
    members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]
    csvStr = ""
    for member in members:
      csvStr = csvStr+ str(getattr(obj, member)) + ","
    csvStr = csvStr[0:-1] + "\n"
    f.write(csvStr)
  f.close()
  print "write finished"

# inputs to URL are:
# Departure Airport
# Arrival Airport
# Departure Date
# Returning Date

# wanted outputs:
# prices
# times of flights
# duration
# number of stops

def getUnitedFlights(departureCode, arrivalCode, departureDate):
 
  debug=True
#  debug=False
  
  url = 'https://www.united.com/ual/en/us/flight-search/book-a-flight/results/rev?f='+departureCode+'&t='+arrivalCode+'&d='+departureDate+'&tt=1&ct=1&sc=7&px=1&taxng=1&idx=1'

  print url


  browser = webdriver.PhantomJS()

  browser.get(url)
  if debug:
    browser.get('file:///Users/athompso/projects/FlightDataGatherer/html.html')
  else:
    browser.get(url)


  print "loading page..."
  
  if not debug:
    time.sleep(17)
  
  priceHistories = []
  flightInfos    = []
  flightStops    = []
  layovers       = []
#while True:

  html = browser.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
  
  
  if not debug and check_link_exists(browser,"fl-results-pagerShowAll"):
#  if check_link_exists(browser,"fl-results-pagerShowAll"):
    browser.find_element_by_id("fl-results-pagerShowAll").click();
    print "getting all results..."
    time.sleep(5)
  
  # debug output
  f = open("html2.out","w") 
  f.write(html.encode('ascii','ignore'))
  f.close()
  
  # these each have one per flight
  fares           = getDataArrayFromClassName(browser, "flight-block-fares-container", ["lowest","Mixed","ticket","Economy","Select"], fareFilter) 
  durations       = getDataArrayFromClassName(browser, "flight-summary-bottom", [], defaultFilter) 
  departureTimes  = getDataArrayFromClassName(browser, "flight-time", [], departureFilter) 
  arrivalTimes    = getDataArrayFromClassName(browser, "flight-time", [], arrivalFilter) 
  nStops          = getDataArrayFromClassName(browser, "flight-connection-container", [], nStopsFilter)  

  # these have multiple per flights
  flightIds         = getDataArrayFromClassNameHidden(browser, 'segment-flight-number')
  planes            = getDataArrayFromClassNameHidden(browser, 'segment-aircraft-type')
  layoverDurations  = getDataArrayFromClassNameHiddenRaw(browser, 'connection-separator')
  flightArriveAndDepartLocation  = getDataArrayFromClassNameHiddenFlights(browser, 'segment-market')

  print "packaging data..."

  curDate =datetime.strftime( datetime.now(), '%Y-%m-%d_%H:%M:%S')

  stopIndex = 0
  layoverIndex = 0
  flightLocationsIndex = 0

  for i in range(0, len(fares)):
    # determine Flight Unique Id
    numStops = int(nStops[i])
    flightIdStr=""
    
    for j in range(stopIndex, stopIndex + numStops + 1):
      flightIdStr= flightIdStr + flightIds[j]
    flightIdStr = flightIdStr + str(departureTimes[i])
    flightUniqueId = hashlib.md5(flightIdStr).hexdigest()  
    
    p = PriceHistory()
    p.flightUniqueId = flightUniqueId
    p.economyFare    = fares[i][0]
    p.businessFare   = fares[i][1]
    p.firstFare      = fares[i][2]
    p.dateOfPrice    = curDate
    priceHistories.append(p)

    fi = FlightInfo()
    fi.flightUniqueId = flightUniqueId
    fi.duration       = durations[i]
    fi.departureTime  = departureTimes[i]
    fi.arrivalTime    = arrivalTimes[i]
    fi.nStops         = nStops[i]
    fi.departureCode  = departureCode
    fi.arrivalCode    = arrivalCode
    fi.airline        = 'United'
    flightInfos.append(fi)
    for j in range(stopIndex, stopIndex + numStops + 1):
     
      locations = []
      if numStops != 0:
        locations = flightArriveAndDepartLocation[flightLocationsIndex].split(' to ')
        flightLocationsIndex = flightLocationsIndex + 1
      else:
        locations.append(departureCode)
        locations.append(departureCode)
      
      fs = FlightStop()
      fs.flightUniqueId = flightUniqueId
      fs.flightNumber   = flightIds[j]
      fs.planeType      = planes[j]
      fs.departureCode  = locations[0]
      fs.arrivalCode    = locations[1]
      flightStops.append(fs)

      if j > stopIndex:
        l = Layover()
        l.flightUniqueId = flightUniqueId
        l.flightNum1     = flightIds[j-1]
        l.flightNum2     = flightIds[j]
        l.duration       = layoverDurations[layoverIndex]
        layovers.append(l) 
        layoverIndex = layoverIndex + 1
    stopIndex = stopIndex + numStops + 1 
  print "data packaged"
  browser.quit()
  return (priceHistories, flightInfos, flightStops, layovers)      

def worker(i, startingDateObj, currDateTime, departureCode, arrivalCode, q):
  print "calling worker"
  currDepartureDateObj = startingDateObj + timedelta(days=i)
  currDepartureDateStr = datetime.strftime(currDepartureDateObj,'%Y-%m-%d')
  print "getting flight data for "+departureCode+" to " + arrivalCode + " on " + currDepartureDateStr 
  tables = getUnitedFlights(departureCode, arrivalCode, currDepartureDateStr)
  print "saving data..."
  q.put(tables)
  for table in tables:
#    q.put(0) #this works...
    if len(table) > 0:
      tableName=type(table[0]).__name__
      saveClassListToCSV("flights_united_"+tableName+"_"+currDepartureDateStr+"_"+currDateTime,table)
    else:
      print "table is empty!"
  print "end worker"
def writerF(q) :
  print "calling writer"
  while True:
    print "writing start loop"
    time.sleep(1)
    #print q.get() # 
    if not q.empty():
      print "getting data"
      q.get() #
      print "got data"
    print "writing end loop"

