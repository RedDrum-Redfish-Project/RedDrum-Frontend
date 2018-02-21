
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

class  RdChassisBackend():
    # class for backend chassis resource APIs
    def __init__(self,rdr):
        self.version=1
        self.rdr=rdr

    # update resourceDB and volatileDict properties
    def updateResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        #self.rdr.logMsg("DEBUG","--------BACKEND updateResourceDBs. updateStaticProps={}".format(updateStaticProps))
        # for testing Front-end, just return--the front-end databases are not updated by the current SIM backend
        return(0,False)
      
    # Reset Chassis sled
    # resetType is a property string (not a dict)
    def doChassisReset(self,chassisid,resetType):
        self.rdr.logMsg("DEBUG","--------BACKEND chassisReset: chassisid: {}, resetType: {}".format(chassisid,resetType))
        return(0)

    # Reseat Chassis sled
    def doChassisOemReseat(self, chassisid):
        self.rdr.logMsg("DEBUG","--------BACKEND chassisReseat: chassisid: {} ".format(chassisid))
        return(0)


    # DO Patch to chassis  (IndicatorLED, AssetTag)
    # patchData is a dict with one property
    #    the front-end will send an individual call for IndicatorLED and AssetTag 
    def doPatch(self, chassisid, patchData):
        # the front-end has already validated that the patchData and chassisid is ok
        # so just send the request here
        self.rdr.logMsg("DEBUG","--------BACKEND Patch chassis data. patchData={}".format(patchData))
        return(0)


    # update Temperatures resourceDB and volatileDict properties
    # returns: rc, updatedResourceDb(T/F).  rc=0 if no error
    def updateTemperaturesResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        self.rdr.logMsg("DEBUG","--------BE updateTemperaturesResourceDBs. updateStaticProps={}".format(updateStaticProps))
        return (0,False)

    # update Fans resourceDB and volatileDict properties
    # returns: rc, updatedResourceDb(T/F).  rc=0 if no error
    def updateFansResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        self.rdr.logMsg("DEBUG","--------BE updateFansResourceDBs. updateStaticProps={}".format(updateStaticProps))
        return (0,False)


    # update Voltages resourceDB and volatileDict properties
    # returns: rc, updatedResourceDb(T/F).  rc=0 if no error
    def updateVoltagesResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        self.rdr.logMsg("DEBUG","--------BE updateVoltagesResourceDBs. updateStaticProps={}".format(updateStaticProps))
        return (0,False)

    # update PowerControl resourceDB and volatileDict properties
    # returns: rc, updatedResourceDb(T/F).  rc=0 if no error
    def updatePowerControlResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        self.rdr.logMsg("DEBUG","--------BE updatePowerControlResourceDBs. ")
        return (0,False)

    # DO Patch to chassis  PowerControl 
    # the front-end will send an individual call for each property
    def patchPowerControl(self, chassisid, patchData):
        self.rdr.logMsg("DEBUG","--------BACKEND Patch chassis PowerControl data. patchData={}".format(patchData))
        return(0)


   # update PowerSupplies resourceDB and volatileDict properties
    #   updated volatiles:  LineInputVoltage, LastPowerOutputWatts, Status
    # returns: rc, updatedResourceDb(T/F).  rc=0 if no error
    def updatePowerSuppliesResourceDbs(self, chassisid, updateStaticProps=False, updateNonVols=True ):
        self.rdr.logMsg("DEBUG","--------BE updatePowerSuppliesResourceDBs. updateStaticProps={}".format(updateStaticProps))
        return (0,False)

