from flightInfo import *
from multiprocessing import Queue, Process
import MySQLdb
import warnings

def writeToSqlDatabase(tables) :
#def writeToSqlDatabase() :
  print "writing to database" 
  db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                       user="root",         # your username
                       passwd="flightInfoDb",  # your password
                       db="flightinfo")        # name of the data base

  warnings.filterwarnings('ignore', category=MySQLdb.Warning)
  cur = db.cursor()

  priceHistories = tables[0]
  for priceHistory in priceHistories:
    query="""INSERT IGNORE INTO PriceHistory (FlightUniqueId, Economy, Business, First, PriceDate)
      VALUES ('"""+str(priceHistory.flightUniqueId) + "'," + str(priceHistory.economyFare) + "," \
      + str(priceHistory.businessFare) + "," + str(priceHistory.firstFare) + ",'" + str(priceHistory.dateOfPrice) + "');"
    cur.execute(query)

  flightInfos = tables[1]
  for flightInfo in flightInfos:
    query="""INSERT IGNORE INTO FLIGHTINFO (FlightUniqueId, Duration, DepartureTime, ArrivalTime, NumStops, DepartureCode, ArrivalCode, Airline)
      VALUES ('"""+str(flightInfo.flightUniqueId) + "','" + str(flightInfo.duration) + "','" + str(flightInfo.departureTime) + \
      "','" + str(flightInfo.arrivalTime) + "'," + str(flightInfo.nStops) + ",'" + str(flightInfo.departureCode) + "','" + str(flightInfo.arrivalCode) + \
      "','" + str(flightInfo.airline) + "');"
    cur.execute(query)

  flightStops=tables[2]
  for flightStop in flightStops:
    query="INSERT IGNORE INTO FlightStop (FlightUniqueId,FlightNumber,PlaneType,DepartureLocation,ArrivalLocation) VALUES ('"+ \
      str(flightStop.flightUniqueId) + "','" + str(flightStop.flightNumber) + "','" + str(flightStop.planeType) + "','" + \
      str(flightStop.departureCode) + "','" + str(flightStop.arrivalCode) + "');"
    cur.execute(query)
    

  layovers=tables[3]
  for layover in layovers:
    query="INSERT IGNORE INTO FlightLayover (FlightUniqueId, FlightNumber1,FlightNumber2,LayoverDuration) VALUES ('" + \
      str(layover.flightUniqueId) + "','" + str(layover.flightNum1) + "','" + str(layover.flightNum2) + "','" + str(layover.duration) + "');"
    cur.execute(query)
  
  db.commit()
  db.close()

def getFlightData(departureAirports, arrivalAirports, startingDate, numDays):


  startingDateObj= datetime.strptime(startingDate, '%Y-%m-%d')
  
  currDateTime = datetime.strftime( datetime.now(), '%Y-%m-%d_%H:%M:%S')
  
  q = Queue()
  procs=[]
  
  
  for departureCode in departureAirports :
    for arrivalCode in arrivalAirports :
      for i in range(0,numDays):
        print "making processes"
        p = Process(target=worker, args=(i, startingDateObj, currDateTime, departureCode, arrivalCode, q,))
        procs.append(p)
#        pp = Process(target=worker, args=(i, startingDateObj, currDateTime, arrivalCode, departureCode, q,))
#        procs.append(pp)
 
  maxThreads=2

  currThreads=0
  tmpProcs = []
  
  metMaxThreads=False
  for proc in procs:
    proc.start()
    time.sleep(5)
    currThreads = currThreads + 1
    tmpProcs.append(proc)
    if currThreads == maxThreads:
      metMaxThreads=True
      for tmpProc in tmpProcs:
        while tmpProc.is_alive():
          time.sleep(10)
          if not q.empty():
            writeToSqlDatabase(q.get())
        tmpProc.join()
      tmpProcs = []
      currThreads = 0
    else:
      metMaxThreads=False

  if not metMaxThreads:
    
    for thread in procs[-1*currThreads:]:
      print "checking alive"
      while thread.is_alive():
        print "is alive"
        time.sleep(10)
        if not q.empty():
          print "writing"
          writeToSqlDatabase(q.get())
      print "joining"
      thread.join()
  
  

