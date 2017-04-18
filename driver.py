import UnitedDriver
import time

while True:
# departure airports
  departureAirports = ["PHL"]
  # arrival airports
  arrivalAirports = ["TYO"]
  
  startingDate = '2017-07-01'
  numDays      = 30
  
  UnitedDriver.getFlightData(departureAirports, arrivalAirports, startingDate, numDays)

  time.sleep(7200)
