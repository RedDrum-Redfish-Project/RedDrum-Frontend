
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import sys
import json

# Backend root class for Simulator
from .chassisBackend   import RdChassisBackend
from .managersBackend  import RdManagersBackend
from .systemsBackend   import RdSystemsBackend

class RdBackendRoot():
    def __init__(self, rdr):
        # initialize data
        self.version = "0.9"
        self.backendStatus=0
        self.discoveryState=0

        # create backend sub-classes
        self.createSubObjects(rdr)

        # run startup tasks
        self.startup(rdr)


    def createSubObjects(self,rdr):
        #create subObjects that implement backend APIs
        self.chassis=RdChassisBackend(rdr)
        self.managers=RdManagersBackend(rdr)
        self.systems=RdSystemsBackend(rdr)
        self.backendStatus=1
        return(0)

    def startup(self,rdr):
        # set the data paths for testing the accountService and sessionService with std linux 
        #   if running w/ -L (isLocal) option, the varDataPath is modified from this by Main
        rdSvcPath=os.getcwd()
        rdr.baseDataPath=os.path.join(rdSvcPath, "reddrum_frontend", "Data")
        #rdr.varDataPath="/var/www/rf"  
        rdr.varDataPath=os.path.join(rdSvcPath, "var", "www", "rf" )
        rdr.RedDrumConfPath=os.path.join(rdSvcPath,  "RedDrum.conf" ) 
        rdr.schemasPath = os.path.join(rdSvcPath, "schemas")

        # note that syslog logging is enabled on Simulator by default unless -L (isLocal) option was specified
        # turn-on console messages also however
        rdr.printLogMsgs=True

        # Simulator uses static Resource Discovery pointing at specified profile, and cached database
        # rdr.rdProfile will point to the specified profile.  This is the dir holding static config
        rdr.useCachedDiscoveryDb=True
        rdr.useStaticResourceDiscovery=True

        self.backendStatus=2
        return(0)

    # runStartupDiscovery is called from RedDrumMain once both the backend and frontend resources have been initialized
    #   it will discover resources and then kick-off any hardware monitors in separate threads
    def runStartupDiscovery(self, rdr):

        # initialize discovery dicts
        rdr.logMsg("INFO"," .... Creating empty resource databases for Chassis, Systems, Managers")
        rdr.root.chassis.chassisDb={}
        rdr.root.chassis.fansDb={}
        rdr.root.chassis.temperatureSensorsDb={}
        rdr.root.chassis.powerSuppliesDb={}
        rdr.root.chassis.voltageSensorsDb={}
        rdr.root.chassis.powerControlDb={}
        rdr.root.managers.managersDb={}
        rdr.root.systems.systemsDb={}
        #rdr.root.mgrNetworkProtocolDb={}
        #rdr.root.mgrEthernetDb={}

        # initialize the volatile dicts
        rdr.logMsg("INFO"," .... Initializing Front-end Volatile databases ")

        # initialize the Chassis volatileDicts
        rdr.logMsg("INFO"," ........ initializing Chassis VolatileDicts")
        rdr.root.chassis.initializeChassisVolatileDict(rdr)

        # initialize the Managers volatileDicts
        rdr.logMsg("INFO"," ........ initializing Managers VolatileDicts")
        rdr.root.managers.initializeManagersVolatileDict(rdr)

        # initialize the Systems volatileDict
        rdr.logMsg("INFO"," ........ initializing Systems VolatileDicts")
        rdr.root.systems.initializeSystemsVolatileDict(rdr)

        rc=0
        return(rc)


    # Backend APIs  
    # POST to Backend
    def postBackendApi(self, request, apiId, rdata):
        # handle backend auth based on headers in request
        # handle specific post request based on apiId and rdata
        rc=0
        statusCode=204
        return(rc,statusCode,"","",{})

    # GET from  Backend
    def getBackendApi(self, request, apiId):
        # handle backend auth based on headers in request
        # handle specific post request based on apiId and rdata
        rc=0
        resp={}
        jsonResp=(json.dumps(resp,indent=4))
        statusCode=200
        return(rc,statusCode,"",jsonResp,{})


