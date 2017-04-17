import UnitedDriver


# departure airports
departureAirports = ["PHL"]

# arrival airports
arrivalAirports = ["TYO"]

startingDate = '2017-05-30'
numDays      = 4

UnitedDriver.getFlightData(departureAirports, arrivalAirports, startingDate, numDays)
