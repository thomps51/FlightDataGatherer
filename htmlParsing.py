from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException  

def getDataArrayFromClassName(browser, className, filterWords , arrayFunc): 
  allLines   = browser.find_elements_by_class_name(className)
  finalArray = []
  for line in allLines:
    text = line.text
    array = text.split('\n')
    itemsToRemove = []
    for ii in range(0,len(array)):
      for test in filterWords:
        item = array[ii]
        if test in item :
          itemsToRemove.append(ii)
  
    itemsToRemove1=list(set(itemsToRemove))
    itemsToRemove1.sort(reverse=True)

    for item in itemsToRemove1:
#      array.remove(item)
      array.pop(item)
    returned = arrayFunc(array)
    if returned is not None:
      finalArray.append(returned)
  return finalArray

def fareFilter(array):
  y = []
  for item in array:
    if "Not available" in item:
      y.append(float(-1))
    else:
      y.append(float(item[1:].replace(",","")))
  return y

def defaultFilter(array):
  return array[0]

def noFilter(array):
  return array

def departureFilter(array):
  if 'Departing' in array[0]:
    if "pm" in array[2]:
      array[2] = array[2].split("pm")[0] + "pm"
    else:
      array[2] = array[2].split("am")[0] + "am"
    return datetime.strptime(array[1] + ' ' + array[2], '%a, %b %d %I:%M %p')

def arrivalFilter(array):
  if 'Arriving' in array[0]:
    if "pm" in array[2]:
      array[2] = array[2].split("pm")[0] + "pm"
    else:
      array[2] = array[2].split("am")[0] + "am"
    return datetime.strptime(array[1] + ' ' + array[2], '%a, %b %d %I:%M %p')

def nStopsFilter(array):
  nums = [int(s) for s in array[-1].split() if s.isdigit()]
  stops = array[0]

  if 'Nonstop' in stops:
    return float(0)
  else:
    return float(nums[0])


def getDataArrayFromClassNameHidden(browser, className): 
  elements = browser.find_elements_by_xpath('//div[@class="'+ className +'"]')
 
  finalArray=[]
  for element in elements: 
    rawStr = str(element.get_attribute('innerHTML')) 
  
    rawStrList = rawStr.splitlines()
  
    for line in rawStrList:
      line  = line.replace('\t','')
      if "span" in line:
        continue
      if len(line) < 2 :
        continue
      finalArray.append(line)
  return finalArray

def getDataArrayFromClassNameHiddenFlights(browser, className): 
  elements = browser.find_elements_by_xpath('//div[@class="'+ className +'"]')
 
  finalArray=[]
  for element in elements: 
    rawStr = str(element.get_attribute('innerHTML')) 
  
    finalArray.append(rawStr)
  return finalArray

def getDataArrayFromClassNameHiddenRaw(browser, className): 
  elements = browser.find_elements_by_xpath('//li[@class="'+ className +'"]')
 
  finalArray=[]
  for element in elements: 
    rawStr = str(element.get_attribute('innerHTML')) 
 
    rawStr = rawStr.replace('<span>','')
    rawStr = rawStr.replace('</span>','')
    rawStr = rawStr.replace(' connection','')

    finalArray.append(rawStr)
  return finalArray

