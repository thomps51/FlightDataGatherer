from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException 
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
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

def convertTime(text):
    hours=''
    minutes=''
    foundHours=False
    for char in text:
        if char.isdigit() and not foundHours:
            hours= hours + char
        elif char == 'h':
            foundHours=True
        elif char.isdigit() and foundHours:
            minutes = minutes + char
    if len(hours) == 0:
        hours="00"
    elif len(hours) == 1:
        hours="0"+hours
    
    if len(minutes) == 0:
        minutes="00"
    elif len(minutes) == 1:
        minutes="0" + minutes
    
    returned=str(hours) + ":" + minutes + ":00"
    return returned

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

def getUnitedFlights(departureCode, arrivalCode, departureDate, urlNum):
 
#  debug=True
    debug=False

    if urlNum == 1:  # economy URL
        url = 'https://www.united.com/ual/en/us/flight-search/book-a-flight/results/rev?f='+departureCode+'&t='+arrivalCode+'&d='+departureDate+'&tt=1&sc=7,7&px=1&taxng=1&idx=1'
    elif urlNum == 2: # business/first URL
        url = 'https://www.united.com/ual/en/us/flight-search/book-a-flight/results/rev?f='+departureCode+'&t='+arrivalCode+'&d='+departureDate+'&tt=1&ct=1&sc=7&px=1&taxng=1&idx=1'

    print(url)

#    browser = webdriver.PhantomJS()
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options() 
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = webdriver.Chrome(executable_path="/Users/athompso/projects/chromedriver",   chrome_options=chrome_options)  
    
    
    browser.get(url)
    if debug:
        browser.get('file:///Users/athompso/projects/FlightDataGatherer/html.html')
    else:
        browser.get(url)

    print("loading page...")
    
    if not debug:
        while True:
            print "testing fares"
            columnElements = browser.find_elements_by_xpath('//div[contains(@class,"fare-column-headers")]//a[@href="#"]')
            if len(columnElements) > 0:
                for line in columnElements:
                    text = line.get_attribute("id")
#                    print text
                print "fares found"
                break
            else:
                print "fares not found.  sleeping..."
                time.sleep(5)

    html = browser.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
    # debug output
    f = open("html3.out","w") 
    f.write(html.encode('ascii','ignore'))
    f.close()



    priceHistories  = []
    flightInfos     = []
    flightStops     = []
    layovers        = []
    if not debug and check_link_exists(browser,"fl-results-pagerShowAll"):
        try:   
            element = browser.find_element_by_id("fl-results-pagerShowAll");
            browser.execute_script("arguments[0].click();", element)
        except ElementNotVisibleException:
            print "ELEMENTNOTVISIBLE not sure what went wrong.  Keep going I guess" 
        print "getting all results..."
        while True:
            print "testing fares"
            try:
                fares = getDataArrayFromClassName(browser, "flight-block-fares-container", ["lowest","Mixed","ticket","Economy","Select"], fareFilter) 
            except:
                fares = []
            if len(fares) > 35:
                print("fares found: ",len(fares[0])) 
                break
            else:
                print "fares not found.  sleeping..."
                time.sleep(5)
    else :
        print "Show all does not exist?"
#    columnsElements = browser.find_elements_by_xpath('//div[contains(@class,"fare-column-headers")]//a[@href="#" and @style]')
#    columnsElements = browser.find_elements_by_xpath('//div[contains(@class,"fare-column-headers")]//a[@href="#"]')
    columnsElements = browser.find_elements_by_xpath('//div[contains(@class,"fare-column-headers")]//a[@href="#"]//div')
#    columnsElements = browser.find_elements_by_xpath('//div[contains(@class,"fare-column-headers")]//a[@href="#"]//div[*]')
    
    
    priceColumns=[]
    for line in columnsElements:
        text = line.text
        newStr=text.replace("\n(lowest)","")
        newStr=newStr.replace("\n"," ")
        priceColumns.append(newStr) 
    print("Price Columns Found: ")
    print(priceColumns)
    
    # case where one column isn't shown
    if not len(priceColumns) == len(fares[0]):
        priceColumns.remove("Economy")
    
    # these each have one per flight
    print("Getting Fares")
    fares = getDataArrayFromClassName(browser, "flight-block-fares-container", ["lowest","Mixed","ticket","Economy","Select"], fareFilter) 
    print("Getting Departure Times")
    departureTimes1 = getDataArrayFromClassName(browser, "flight-time", [], departureFilter) 
    departureTimes = []
#conver depature time
    years=datetime.strptime(departureDate, '%Y-%m-%d').year
    for departureTime in departureTimes1:
        departureTime = departureTime.replace(year=years)
        departureTimes.append(departureTime)
    
    print("Getting Arrival Times")
    arrivalTimes  = []
    arrivalTimes1 = getDataArrayFromClassName(browser, "flight-time", [], arrivalFilter) 
    for arrivalTime in arrivalTimes1:
        arrivalTime = arrivalTime.replace(year=years)
        arrivalTimes.append(arrivalTime)
    
    print("Getting Number of Stops")
    nStops                  = getDataArrayFromClassName(browser, "flight-connection-container", [], nStopsFilter)  

    # these have multiple per flights
    print("Getting Flight Ids")
    flightIds           = getDataArrayFromClassNameHidden(browser, 'segment-flight-number')
    print("Getting Plane Types")
    planes              = getDataArrayFromClassNameHidden(browser, 'segment-aircraft-type')
    print("Getting Layover Durations")
    layoverDurations1   = getDataArrayFromClassNameHiddenRaw(browser, 'connection-separator')
 
    layoverDurations = []
    for duration in layoverDurations1:
        timeText = convertTime(duration)
        layoverDurations.append(timeText)
    
    print("Getting Locations")
    flightArriveAndDepartLocation  = getDataArrayFromClassNameHiddenFlights(browser, 'segment-market')


    print("Getting Durations")
    elements = browser.find_elements_by_xpath('//a[@class="'+ 'flight-duration otp-tooltip-trigger' +'"]')
    durations=[]
    for line in elements:
        text = line.text
        timeText = convertTime(text)
        durations.append(timeText)
        
    print "packaging data..."

    curDate =datetime.strftime( datetime.now(), '%Y-%m-%d_%H:%M:%S')

    stopIndex = 0
    layoverIndex = 0
    flightLocationsIndex = 0

    for i in range(0, len(fares)):
        # determine Flight Unique Id
        numStops = int(nStops[i])
        flightIdStr=""
 
        flag = False
        for j in range(stopIndex, stopIndex + numStops + 1):
            if j>= len(flightIds) :
                    flag=True
                    continue
            flightIdStr= flightIdStr + flightIds[j]
        if flag :
            break
        flightIdStr = flightIdStr + str(departureTimes[i])
        flightUniqueId = hashlib.md5(flightIdStr).hexdigest()  
        
        p = PriceHistory()
        p.flightUniqueId = flightUniqueId
        
        try :
            indexEconomy     = priceColumns.index("Economy")
            
            if fares[i][indexEconomy]  < 0 :
                try :
                    indexEconomyFlex = priceColumns.index("Economy (flexible)")
                    p.economyFare    = fares[i][indexEconomyFlex]
                except ValueError:
                    p.economyFare    = fares[i][indexEconomy]
            else:
                p.economyFare        = fares[i][indexEconomy]
            
        except ValueError:
            print("no economy found!")
            p.economyFare        = -1.0
        
        try :
            index = priceColumns.index("Business")
            p.businessFare       = fares[i][index]
        except ValueError:
            print("no business found!")
            p.businessFare        = -1.0

        try: 
            index = priceColumns.index("First")
            p.firstFare          = fares[i][index]
        except ValueError: 
            print("no first found!")
            p.firstFare          = -1

        p.dateOfPrice        = curDate
        priceHistories.append(p)

        fi = FlightInfo()
        fi.flightUniqueId   = flightUniqueId
        fi.duration         = durations[i]
        fi.departureTime    = departureTimes[i]
        fi.arrivalTime      = arrivalTimes[i]
        fi.nStops           = nStops[i]
        fi.departureCode    = departureCode
        fi.arrivalCode      = arrivalCode
        fi.airline          = 'United'
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
            fs.flightNumber     = flightIds[j]
            fs.planeType        = planes[j]
            fs.departureCode    = locations[0]
            fs.arrivalCode      = locations[1]
            flightStops.append(fs)

            if j > stopIndex:
                l = Layover()
                l.flightUniqueId = flightUniqueId
                l.flightNum1         = flightIds[j-1]
                l.flightNum2         = flightIds[j]
                if layoverIndex >= len(layoverDurations) :
                    print "ERROR: incorrect number of layovers on page" 
                    print str(layoverIndex) + " " + str(len(layoverDurations))
                    continue
                l.duration           = layoverDurations[layoverIndex]
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
    

    tablesEcon   = getUnitedFlights(departureCode, arrivalCode, currDepartureDateStr, 1)
    tablesBusin  = getUnitedFlights(departureCode, arrivalCode, currDepartureDateStr, 2)

    # merge tables
    for ii in range(0,len(tablesEcon[0])):
        uniqueId = tablesEcon[0][ii].flightUniqueId
        for jj in range(0,len(tablesBusin[0])) :
            if tablesBusin[0][jj].flightUniqueId == uniqueId :
                tablesEcon[0][ii].businessFare  = tablesBusin[0][jj].businessFare
                tablesEcon[0][ii].firstFare     = tablesBusin[0][jj].firstFare
                break


    print "saving data..."
    print "# tables: " + str(len(tablesEcon[0]))
    q.put(tablesEcon)
#  for table in tables:
##      q.put(0) #this works...
#        if len(table) > 0:
#            tableName=type(table[0]).__name__
#            saveClassListToCSV("flights_united_"+tableName+"_"+currDepartureDateStr+"_"+currDateTime,table)
#        else:
#            print "table is empty!"
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

