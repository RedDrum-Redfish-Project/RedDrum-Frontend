
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

class  RdSystemsBackend():
    # class for backend systems resource APIs
    def __init__(self,rdr):
        self.version=1
        self.rdr=rdr

    # update resourceDB and volatileDict properties
    def updateResourceDbs(self,systemid, updateStaticProps=False, updateNonVols=True ):
        # for the simulator, just return (0,False).   The Sim backend currently doesnt update resources after discovery
        return(0,False)


    # DO action:   Reset 
    def doSystemReset(self,systemid,resetType):
        self.rdr.logMsg("DEBUG","--------SIM BACKEND systemReset. resetType={}".format(resetType))
        return(0)


    # DO Patch to System  (IndicatorLED, AssetTag, or boot overrides
    # the front-end will send an individual call for IndicatorLED and AssetTag or bootProperties
    # multiple boot properties may be combined in one patch
    def doPatch(self, systemid, patchData):
        # the front-end has already validated that the patchData and systemid is ok
        # so just send the request here
        self.rdr.logMsg("DEBUG","--------BACKEND Patch system data. patchData={}".format(patchData))
        return(0)


    # update ProcessorsDb 
    def updateProcessorsDbFromBackend(self, systemid, procid=None, noCache=False ):
        return(0)

    # update MemoryDb 
    def updateMemoryDbFromBackend(self, systemid, memid=None, noCache=False ):
        return(0)

    # update SimpleStorageDb 
    def updateSimpleStorageDbFromBackend(self, systemid, cntlrid=None, noCache=False ):
        return(0)

    # update EthernetInterfaceDb 
    def updateEthernetInterfaceDbFromBackend(self, systemid, ethid=None, noCache=False ):
        # for the simulator, just return (0).   The Sim backend currently doesnt update resources after discovery
        return(0)
