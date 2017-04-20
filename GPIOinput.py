#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# GPIO Input read daemon
#
# This script reads GPIO input pins and updates corresponding virtual switches in Domoticz
#
# Each input must have a corresponding virtual switch defined in Domoticz. See Domoticz Wiki how to do this. The switch type must be 'On/Off'. 'Contact' doesn't work.
# The switch - input pin mapping is done by adding the following keyword in the switch description field:
# 
# %pin=<n>      where n should be replaced by the corresponding BCM pin number.
#
# Example:
# %pin=17
# 
# 
# Various option can be set by command line parameters.
#
# python GPIOinput.py -h
#
# will explain the options.
#

##############################################################################################################################################
import time,re
import urllib2, json, argparse
import RPi.GPIO as GPIO
 
DOMOTICZ_URL="http://localhost:8085"
USERNAME =""
PASSWORD=""
LOGFILE="./GPIOinput.log"
VERBOSE= False
WAIT = 10                   # seconds between loops
DETECT_WAIT = 60            # seconds between new detection of switches


    

def get_cmd_line_parameters():

    global  DOMOTICZ_URL,USERNAME,PASSWORD,LOGFILE,WAIT,DETECT_WAIT,VERBOSE

    parser = argparse.ArgumentParser( description='GPIO input read daemon' )
    parser.add_argument("-v", "--verbose", help="Verbose logging", action ="store_true")
    parser.add_argument("-u","--url", help="Domoticz server. Default "+ DOMOTICZ_URL, default=DOMOTICZ_URL)
    parser.add_argument("-n","--uname", help="username Domoticz server",default=USERNAME)
    parser.add_argument("-x","--password", help="password Domoticz server",default=PASSWORD)
    parser.add_argument("-l","--logfile", help="Log file. Default " + LOGFILE, default=LOGFILE)
    parser.add_argument("-w","--wait", help="Wait <n> seconds between readings. Default "+str(WAIT)+"s",type=int,default=WAIT)
    parser.add_argument("-W","--wait_detect", help="Wait <n> seconds between new detection of switches. Default "+str(DETECT_WAIT)+"s",type=int,default=DETECT_WAIT)

    
                        
    args = parser.parse_args()
    DOMOTICZ_URL = args.url
    USERNAME = args.uname
    PASSWORD = args.password
    LOGFILE = args.logfile
    WAIT = int(args.wait)
    DETECT_WAIT= int(args.wait_detect)
    VERBOSE=args.verbose

    
    
def GPIOinput_logger(name,level):
    
    import logging, logging.handlers  
    
    handler = logging.handlers.RotatingFileHandler(name,maxBytes=200000,backupCount=10)     # create a file handler
    handler.setLevel(logging.DEBUG)                                                         # set level - do not change this!
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')   # define logging format
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)   
    logger.addHandler(handler)                                                         # add the handler to the logger
                            
    if level.upper() == "DEBUG" :
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    return logger

def getPort(p):

    data=GPIO.input(p)
    return data
    
def updateDomoticz(idx, data) :

    global  opener
    
    url= DOMOTICZ_URL+"/json.htm?type=command&param=udevice&idx=" +str(idx)+"&nvalue="+str(data)
    response=opener.open(url)
    return response

    
def findInputPins() :

    global pLogger,opener
    
    url= DOMOTICZ_URL+"/json.htm?type=devices&filter=light&used=true&order=Name"
    pLogger.debug('Reading from %s',url)
    
    response=opener.open(url)
    data=json.loads(response.read())
    pins=[]
    for x in data["result"] :
        if x["Description"].find("%pin") != -1 :
            no=[w for w in re.split('%pin=|,| ',x["Description"]) if w] [0]
            GPIO.setup(int(no), GPIO.IN )
            pins.append([ {'idx': x['idx'],'Name': x['Name'],'Pin': no,'Val' : 0}])

            

    return pins
    
def update_old_data(old,new) :

    for x in new :
        for y in old :
            if x[0]["Pin"] == y[0]["Pin"] :
               x[0]["Val"] == y[0]["Val"]       # pin not new - copy value from old data
    
    return new                                  # return the new and updated list

def main():

 
    global  pLogger,opener 
    
    GPIO.setmode(GPIO.BCM)


    get_cmd_line_parameters()           # get command line options 
    
    if VERBOSE :
        pLogger=GPIOinput_logger(LOGFILE, "Debug")
    else :
        pLogger=GPIOinput_logger(LOGFILE, "Info")

    #
    #   build authentication strings to  access Domoticz server(s)
    #
    p = urllib2.HTTPPasswordMgrWithDefaultRealm()
    p.add_password(None, DOMOTICZ_URL, USERNAME, PASSWORD)
    handler = urllib2.HTTPBasicAuthHandler(p)
    opener = urllib2.build_opener(handler)
    
    pLogger.info("*** GPIO digital input read system is starting up ***")
    pLogger.info("Domoticz server URL: %s, username: %s, password: %s, logfile: %s, wait between readings: %s (s), wait between switch detection: %s, (s)", DOMOTICZ_URL,USERNAME,PASSWORD,LOGFILE,str(WAIT),str(DETECT_WAIT))
   
    n=0
    old_data=[]
    while True :
        if n == 0  :
            inputPins= findInputPins()          # scan all switch devices and build array of input pins
            pLogger.debug(inputPins) 
            updated_data=update_old_data(old_data,inputPins)    # update list of old data with new input pins (if any)
            if updated_data != old_data :
                old_data = updated_data
                for x in old_data : pLogger.info("Switch found, idx: %s, Name: %s, GPIO pin (BCM): %s", x[0]['idx'].ljust(3),x[0]['Name'].ljust(15)[:15], x[0]['Pin'].ljust(2) )
                pLogger.info("********************************************************************************************")              
        n=n+1
        if n >= DETECT_WAIT/WAIT : n=0

        for x in inputPins :
            data=getPort(int(x[0]["Pin"]))
            for y in old_data :
                if y[0]["Pin"]==x[0]["Pin"] :
                    if data != y[0]["Val"] :
                        y[0]["Val"] = data
                        updateDomoticz(x[0]["idx"],data)
                        pLogger.info("Input read and switch updated. idx: %s,  Name: %s, GPIO pin (BCM): %s, data: %s ", x[0]['idx'].ljust(3),x[0]['Name'].ljust(15)[:15], x[0]['Pin'].ljust(2),str(data ))  
                        pLogger.info("--------------------------------------------------------------------------------------------")
        time.sleep(WAIT)
        
main();
        
       
