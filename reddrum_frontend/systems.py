
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys
import datetime
from .redfish_headers import RfAddHeaders


class RfSystemsResource():       
    # Class for all resources under /redfish/v1/Systems
    # Note that this resource was created in serviceRoot for the Systems Resource.
    def __init__(self,rfr ):
        self.rfr=rfr
        self.systemsDbDiscovered=None
        self.loadResourceTemplates(rfr )
        self.loadSystemsDbFiles(rfr)
        sys.stdout.flush()
        self.hdrs=RfAddHeaders(rfr)
        self.staticProperties=["Name","Description","SystemType","Manufacturer","Model","SKU","SerialNumber","PartNumber","UUID"]
        self.nonVolatileProperties=[ "AssetTag","HostName","BiosVersion" ]
        self.bootSourceVolatileProperties=["BootSourceOverrideEnabled","BootSourceOverrideMode","BootSourceOverrideTarget",
                              "UefiTargetBootSourceOverride"]

    #TODO xg99
    #  Action "SetDefaultBootOrder"

    def loadResourceTemplates( self, rfr ):
        # these are very bare-bones templates but we want to be able to update the resource version or context easily
        #   so the approach is to always start with a standard template for each resource type

        #load SystemsCollection Template
        self.systemsCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ComputerSystemCollection.json")

        #load SystemsEntry Template
        self.systemsEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ComputerSystem.json")

        #load sub-Collection Templates
        self.processorsCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ProcessorCollection.json")
        self.simpleStorageCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", 
                                                               "SimpleStorageCollection.json")
        self.ethernetInterfaceCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", 
                                                               "EthernetInterfaceCollection.json")
        self.memoryCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "MemoryCollection.json")

        #load sub-collection Entry Templates
        self.processorEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Processor.json")
        self.simpleStorageEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "SimpleStorage.json")
        self.ethernetInterfaceEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "EthernetInterface.json")
        self.memoryEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Memory.json")

    # worker function called by loadResourceTemplates() to load a specific template
    # returns a dict loaded with the template file
    # if file does not exist, the service exits
    #    assumes good json in the template file
    def loadResourceTemplateFile( self, dataPath, subDir, filename ):
        filePath=os.path.join(dataPath, subDir, filename)
        if os.path.isfile(filePath):
            response=json.loads( open(filePath,"r").read() )
            return(response)
        else:
            self.rfr.logMsg("CRITICAL", "*****System Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
            sys.exit(10)

        

    def loadSystemsDbFiles(self,rfr ):
        # if rfr.resourceDiscoveryUseDbCache is True:
        #   then if the systems database files exist in /var/www/rf/systemsDb/* then load them to in-memory dict
        self.systemsDbDiscovered=False
        if rfr.useCachedDiscoveryDb is True:
            # first make sure all of the systems DB files exist
            systemsDbCacheExists=True
            sysDbFiles=["SystemsDb.json","ProcessorsDb.json","SimpleStorageDb.json","EthernetInterfacesDb.json","MemoryDb.json"]
            for filenm in sysDbFiles:
                sysDbFilePath=os.path.join(rfr.varDataPath,"systemsDb", filenm)
                if not os.path.isfile(sysDbFilePath):
                    systemsDbCacheExists = False
                    break
            # then load them into dictionaries
            if systemsDbCacheExists is True:
                self.systemsDb=self.loadSystemsDbFile(rfr.varDataPath, "systemsDb", "SystemsDb.json",True) 
                self.processorsDb=self.loadSystemsDbFile(rfr.varDataPath, "systemsDb", "ProcessorsDb.json",False) 
                self.simpleStorageDb=self.loadSystemsDbFile(rfr.varDataPath, "systemsDb", "SimpleStorageDb.json",False) 
                self.ethernetInterfaceDb=self.loadSystemsDbFile(rfr.varDataPath, "systemsDb", "EthernetInterfacesDb.json",False) 
                self.memoryDb=self.loadSystemsDbFile(rfr.varDataPath, "systemsDb", "MemoryDb.json",False) 
                self.systemsDbDiscovered=True

        return(0)

    # worker function to load CACHED systems db file into dict
    def loadSystemsDbFile( self, dataPath, subDir, filename, requiredFlag ):
        filePath=os.path.join(dataPath, subDir, filename)
        if os.path.isfile(filePath):
            response=json.loads( open(filePath,"r").read() )
            return(response)
        else:
            if requiredFlag is True:
                self.rfr.logMsg("CRITICAL","*****Systems Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
                sys.exit(10)
            else:
                return(0)


    # clear the current Systems Db Dicts and HDD caches
    def clearSystemsResourceCaches(self,rfr):
        self.systemsDb=self.clearSystemsDbFile(rfr, "systemsDb", "SystemsDb.json") 
        self.processorsDb=self.clearSystemsDbFile(rfr, "systemsDb", "ProcessorsDb.json") 
        self.simpleStorageDb=self.clearSystemsDbFile(rfr, "systemsDb", "SimpleStorageDb.json") 
        self.ethernetInterfaceDb=self.clearSystemsDbFile(rfr, "systemsDb", "EthernetInterfacesDb.json") 
        self.memoryDb=self.clearSystemsDbFile(rfr, "systemsDb", "MemoryDb.json") 
        self.systemsDbDiscovered=False


    # worker function for above clear systems resource caches 
    def clearSystemsDbFile( self, rfr, subDir, filename ):
        clearedDb=dict()
        varDbFilePath=os.path.join(rfr.varDataPath, subDir, filename)
        #jsonEmptyDb=json.dumps(clearedDb,indent=4)
        #with open( varDbFilePath, 'w', encoding='utf-8') as f:
        #    f.write(jsonEmptyDb)
        if os.path.exists(varDbFilePath):
            os.remove(varDbFilePath)        
        return(clearedDb)

    # functions to save the systems Db dicts to their persistent files
    def updateStaticSystemsDbFile( self ):
        rc=self.updateStaticSystemsDbResourceFile(self.systemsDb,"SystemsDb.json") 
        return(rc)

    def updateStaticProcessorsDbFile( self ):
        rc=self.updateStaticSystemsDbResourceFile(self.processorsDb,"ProcessorsDb.json") 
        return(rc)

    def updateStaticStorageDbFile( self ):
        rc=self.updateStaticSystemsDbResourceFile(self.simpleStorageDb,"SimpleStorageDb.json") 
        return(rc)

    def updateStaticEthernetInterfacesDbFile( self ):
        rc=self.updateStaticSystemsDbResourceFile(self.ethernetInterfaceDb,"EthernetInterfacesDb.json") 
        return(rc)

    def updateStaticMemoryDbFile( self ):
        rc=self.updateStaticSystemsDbResourceFile(self.memoryDb,"MemoryDb.json") 
        return(rc)

    # worker function to write the various systems Db Dicts back to the persistant systems db file caches
    def updateStaticSystemsDbResourceFile( self, resDb, resDbFile ):
        varDbFilePath=os.path.join(self.rfr.varDataPath, "systemsDb", resDbFile )
        responseJson=json.dumps(resDb, indent=4)
        with open( varDbFilePath, 'w', encoding='utf-8') as f:
            f.write(responseJson)
        return(0)




    def initializeSystemsVolatileDict(self,rfr):
        # this is the in-memory dict of volatile systems properties
        # the systemsDict is an dict indexed by   systemsDict[systemid][<systemsParameters>]
        #   self.systemsVolatileDict[systemid]= a subset of the volatile systems properties
        #       subset of: volatileProperties=["IndicatorLED", "PowerState" ] and "Status"
        #       subset of: {"IndicatorLED": <led>, "PowerState": <ps>, "Status":{"State":<s>,"Health":<h>}} 
        self.systemsVolatileDict=dict()   #create an empty dict of Systems entries

        # initialize the Volatile Dicts
        for systemid in self.systemsDb:
            # inialize with empty members for all known systems
            self.systemsVolatileDict[systemid]={}



    # GET Systems Collection 
    def getSystemsCollectionResource(self, request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.systemsCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # first copy the systems Collection template 
        # then update the Members array for each system previously discovered--in SystemsDb 

        # copy the systemsCollection template file (which has an empty roles array)
        responseData2=dict(self.systemsCollectionTemplate)
        count=0
        # now walk through the entries in the systemsDb and build the systemsCollection Members array
        # note that the members array is an empty array in the template
        uriBase="/redfish/v1/Systems/"
        for systemid in self.systemsDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=uriBase + systemid
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)


    # GET System Entry 
    def getSystemEntry(self, request, systemid):
        # generate error header for 4xx errors
        errhdrs=self.hdrs.rfRespHeaders(request)

        # verify that the systemid is valid
        if systemid not in self.systemsDb:
                return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="GetPatch",
                                     resource=self.systemsEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.systemsEntryTemplate)

        # setup some variables to build response from
        basePath="/redfish/v1/Systems/"
        #self.staticProperties=["Name","Description","SystemType","Manufacturer","Model","SKU","SerialNumber","PartNumber","UUID"]
        #self.nonVolatileProperties=[ "AssetTag","HostName","BiosVersion" ]
        volatileProperties=[ "IndicatorLED", "PowerState"]
        statusSubProperties=["State", "Health", "HealthRollup"]
        #self.bootSourceVolatileProperties=["BootSourceOverrideEnabled","BootSourceOverrideMode","BootSourceOverrideTarget",
        #                      "UefiTargetBootSourceOverride"]
        # nonVol procSummary and memSummary
        processorSummaryProps=["Count", "Model", "Status" ]
        memorySummaryProps=["TotalSystemMemoryGiB","MemoryMirroring","Status"]

        baseNavProperties=[ "Processors","EthernetInterfaces","SimpleStorage","Memory", "SecureBoot","Bios", "Storage"
                      "NetworkInterfaces", "LogServices" ]
        arrayBaseNavProperties=[ "PCIeDevices", "PCIeFunctions" ]

        #linkNavProperties=["ManagedBy","Chassis","PoweredBy","CooledBy","EndPoints"] # xg some not supported
        linkNavProperties=["ManagedBy","Chassis", "PoweredBy", "CooledBy"] # xg Only managedBy and Chassis supported

        # assign the required properties
        responseData2["@odata.id"] = basePath + systemid
        responseData2["Id"] = systemid

        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        rc=self.updateResourceDbsFromBackend(systemid)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getSystemEntry(): updateResourceDbsFromBackend() returned error ")
            return(9, 500, "Internal Error", "", errhdrs)

        # get the base static properties that were assigned when the resource was created
        for prop in self.staticProperties:
            if prop in self.systemsDb[systemid]:
                responseData2[prop] = self.systemsDb[systemid][prop]

        # get the base non-volatile properties that were assigned when the resource was created
        # these are stored in the persistent cache but are not static--ex is assetTag
        for prop in self.nonVolatileProperties:
            if prop in self.systemsDb[systemid]:
                responseData2[prop] = self.systemsDb[systemid][prop]

        # get the volatile properties eg powerState
        volatileProps = self.getVolatileProperties(volatileProperties, None, None,
                        self.systemsDb[systemid], self.systemsVolatileDict[systemid])
        for prop in volatileProps:
            responseData2[prop] = volatileProps[prop]

        # get the status properties
        statusProps = self.getStatusProperties(statusSubProperties, None, None,
                      self.systemsDb[systemid], self.systemsVolatileDict[systemid])
        for prop in statusProps:
            responseData2[prop] = statusProps[prop]

        # set the base navigation properties:   /redfish/v1/Systems/<baseNavProp>
        for prop in baseNavProperties:
            if "BaseNavigationProperties"  in  self.systemsDb[systemid]:
                if prop in self.systemsDb[systemid]["BaseNavigationProperties"]:
                    responseData2[prop] = { "@odata.id": basePath + systemid + "/" + prop }

        # set the ARRAY-type base navigation properties:   /redfish/v1/Systems/<arrayBaseNavProp>
        # creates URIs /redfish/v1/<sysid>/PCIeDevices/<id>, and /redfish/v1/<sysid>/PCIeFunctions/<id>" 
        #  but the <id> here can have "/"s eg "NIC/Functions/1"
        for prop in arrayBaseNavProperties:
            if "ArrayBaseNavigationProperties"  in  self.systemsDb[systemid]:
                if prop in self.systemsDb[systemid]["ArrayBaseNavigationProperties"]:
                    arrayMembers=dict()
                    propVal=self.systemsDb[systemid]["ArrayBaseNavigationProperties"][prop]
                    for ii in range(0,len(prop)):
                        memberii = { "@odata.id": basePath + systemid + "/" + prop + "/" + propVal[ii] }
                        arrayMembers.append(memberii)
                    responseData2[prop] = arrayMembers

        # build the Actions data
        if "ActionsResetAllowableValues" in self.systemsDb[systemid]:
            resetAction = { "target": basePath + systemid + "/Actions/ComputerSystem.Reset",
                            "ResetType@Redfish.AllowableValues": self.systemsDb[systemid]["ActionsResetAllowableValues"] }
            if "Actions" not in responseData2:
                responseData2["Actions"]={}
            responseData2["Actions"]["#ComputerSystem.Reset"]= resetAction


        # build Dell OEM Section (Sleds only)
        if "OemDellG5MCBmcInfo" in self.systemsDb[systemid]:
            # define the legal oem properties
            oemDellG5NonVolatileProps = [ "BmcVersion", "BmcIp", "BmcMac" ]
            oemDellG5MgtNwNonVolatileProps=["MgtNetworkIP","MgtNetworkMAC","MgtNetworkEnableStatus","MgtNetworkLinkStatus"]
            oemNetloc="MgtNetworkNetloc"

            # check if each of the legal oem subProps are in the db
            oemData={}
            for prop in oemDellG5NonVolatileProps:
                if prop in self.systemsDb[systemid]["OemDellG5MCBmcInfo"]:
                    # since these sub-props are nonVolatile, read them from the database
                    oemData[prop] = self.systemsDb[systemid]["OemDellG5MCBmcInfo"][prop]

            if "OemDellG5MgtNetworkInfo" in self.systemsDb[systemid]:
                # check if each of the legal oem subProps are in the db
                for prop in oemDellG5MgtNwNonVolatileProps:
                    if prop in self.systemsDb[systemid]["OemDellG5MgtNetworkInfo"]:
                        # since these sub-props are nonVolatile, read them from the database
                        oemData[prop] = self.systemsDb[systemid]["OemDellG5MgtNetworkInfo"][prop]
            if oemNetloc in self.systemsDb[systemid]:
                oemData[oemNetloc]= self.systemsDb[systemid][oemNetloc]

            oemData["@odata.type"] = "#DellG5MC.v1_0_0.ComputerSystem"
            if "Oem" not in responseData2:
                responseData2["Oem"]={}
            responseData2["Oem"]["Dell_G5MC"] = oemData

            # add Dell PowerEdge OEM data
            if "OemDell" in self.systemsDb[systemid]:
                if "Oem" not in responseData2:
                    responseData2["Oem"]={}
                responseData2["Oem"]["Dell"] = self.systems[Db][systemid]["OemDell"]

        # build Intel Rackscale OEM Section 
        if "OemRackScaleSystem" in self.systemsDb[systemid]:
            oemRackScaleProps = ["ProcessorSockets","MemorySockets","DiscoveryState" ]

            # check if each of the legal oem subProps are in the db
            oemData = {"@odata.type": "#Intel.Oem.ComputerSystem" }
            for prop in oemRackScaleProps:
                if prop in self.systemsDb[systemid]["OemRackScaleSystem"]:
                    # since these sub-props are nonVolatile, read them from the database
                    if prop == "DiscoveryState":
                        if self.rfr.rsaDeepDiscovery is True:
                            oemData["DiscoveryState"]="Basic"
                    else:
                        oemData[prop] = self.systemsDb[systemid]["OemRackScaleSystem"][prop]
            if "Oem" not in responseData2:
                responseData2["Oem"]={}
            responseData2["Oem"]["Intel_RackScale"] = oemData

        # generate system UUID using Redfish Service UUID if sysDb says to
        # if GetUuidFromServiceRoot is True, use ServiceRoot UUID for system UUID
        if ("UUID" not in responseData2) and ("GetUuidFromServiceRoot" in self.systemsDb[systemid]):
            if self.systemsDb[systemid]["GetUuidFromServiceRoot"] is True:
                responseData2["UUID"] = self.rfr.root.resData["UUID"]


        # build the navigation properties under Links : "Contains", "ContainedBy", ManagersIn...
        responseData2["Links"]={}
        for navProp in linkNavProperties:
            if navProp in self.systemsDb[systemid]:
                    if( navProp == "ManagedBy"):
                        linkBasePath="/redfish/v1/Managers/"
                    elif( navProp == "Chassis"):    # it is the /redfishg/v1/Chassis/
                        linkBasePath="/redfish/v1/Chassis/"
                    else:
                        pass

                    #start with an empty array
                    members = list()
                    # now create the array of members for this navProp
                    for memberId in self.systemsDb[systemid][navProp]:
                        newMember= { "@odata.id": linkBasePath + memberId }
                        members.append(newMember)
                    # now add the members array to the response data
                    responseData2["Links"][navProp] = members

        # get the Boot complex property 
        if "BootSourceAllowableValues" in self.systemsDb[systemid]:
            bootData={ "BootSourceOverrideTarget@Redfish.AllowableValues": self.systemsDb[systemid]["BootSourceAllowableValues"] }
            for prop in self.bootSourceVolatileProperties:
                if prop in self.systemsDb[systemid]["BootSourceVolatileProperties"]:
                    if prop in self.systemsVolatileDict[systemid]:
                        bootData[prop]=self.systemsVolatileDict[systemid][prop]
                    elif prop in self.systemsDb[systemid]:  #default  
                        self.systemsVolatileDict[systemid][prop] = self.systemsDb[systemid][prop]
                        bootData[prop]=self.systemsVolatileDict[systemid][prop]
                    else:
                        bootData[prop]=None
            responseData2["Boot"]=bootData

        # get the ProcessorSummary data
        #   FYI processorSummaryProps=["Count", "Model", "Status" ]
        procData = dict()
        if "ProcessorSummary" in self.systemsDb[systemid]:
            procData=dict()
            for prop in processorSummaryProps:
                if prop in self.systemsDb[systemid]["ProcessorSummary"]:
                    procData[prop]=self.systemsDb[systemid]["ProcessorSummary"][prop]
            responseData2["ProcessorSummary"]=procData
                
        # get the MemorySummary data
        #   FYI memorySummaryProps=["TotalSystemMemoryGiB","MemoryMirroring","Status"]
        memData=dict()
        if "MemorySummary" in self.systemsDb[systemid]:
            memData=dict()
            for prop in memorySummaryProps:
                if prop in self.systemsDb[systemid]["MemorySummary"]:
                    memData[prop]=self.systemsDb[systemid]["MemorySummary"][prop]
            responseData2["MemorySummary"]=memData

        # get the TrustedModules and HostWatchdogTimer Complex types
        if "TrustedModules" in self.systemsDb[systemid]: # this is an array of trusted modules?
            responseData2["TrustedModules"]=self.systemsDb[systemid]["TrustedModules"]
        if "HostWatchdogTimer" in self.systemsDb[systemid]:
            responseData2["HostWatchdogTimer"]=self.systemsDb[systemid]["HostWatchdogTimer"]

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "SUCCESS", jsonRespData2, respHdrs)



    # PATCH System Entry
    def patchSystemEntry(self, request, systemid, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the systemid is valid
        if systemid not in self.systemsDb:
            return(4, 404, "Not Found","", hdrs)

        #define the patchable properties in Systems Resource
        patchableInRedfish=["AssetTag","IndicatorLED"]
        bootSourcePatchableInRedfish=["BootSourceOverrideEnabled","BootSourceOverrideMode","BootSourceOverrideTarget",
                                       "UefiTargetBootSourceOverride" ]

        #first verify client didn't send us a property we cant patch based on Redfish Schemas
        for prop in patchData:
            if( prop == "Boot" ):
                for subProp in patchData["Boot"]:
                    if subProp not in bootSourcePatchableInRedfish:
                        return(4, 400, "Bad Request: Property: \"Boot\": {} not patachable per Redfish Spec".format(subProp),"", hdrs)
            elif prop not in patchableInRedfish: 
                return(4, 400, "Bad Request: Property: {} not patachable per Redfish Spec".format(prop),"", hdrs)

        #second check if this instance of systems allows the patch data to be patched
        #  if there is no Patchable property in systemsDb, then nothing is patchable
        if "Patchable" not in self.systemsDb[systemid]:
            return(4, 400, "Bad Request: Resource is not patachable","", hdrs)

        # check if the specific property is patchable
        for prop in patchData:
            if( prop == "Boot" ):
                if "BootSourcePatchableProperties" not in self.systemsDb[systemid]:
                    return(4, 400, "Bad Request: Property: \"Boot\" not patachable for this resource","", hdrs)
                for subProp in patchData["Boot"]:
                    if subProp not in self.systemsDb[systemid]["BootSourcePatchableProperties"]:
                        return(4, 400, "Bad Request: Property: \"Boot\": {} not patachable for this resource".format(subProp),"", hdrs)
            elif prop not in self.systemsDb[systemid]["Patchable"]:
                return(4, 400, "Bad Request: Property: {} not patachable for this resource".format(prop),"", hdrs)

        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        rc=self.updateResourceDbsFromBackend(systemid)
        if( rc != 0):
            self.rfr.logMsg("Error","patchSystemEntry(): updateResourceDbsFromBackend returned error ")
            return(5, 500, "Internal Error: Error getting resource Update from Backend", "", hdrs)

        # now construct the patch data, and update the volatileDict or resourceDb
        # send separate patches for each patch property, 
        # if patch property is Boot, send all of the subprops under Boot together
        updateSystemsDb=False
        bootPatchData={}
        for prop in patchData:
            if( prop == "Boot" ):
                if prop not in self.systemsVolatileDict[systemid]:
                    self.systemsVolatileDict[systemid][prop]={}
                for subProp in patchData[prop]:
                    # update the volatile dict
                    self.systemsVolatileDict[systemid][subProp]=patchData[prop][subProp]
                    # construct the boot patch data
                    bootPatchData[subProp]=patchData[prop][subProp]
                reqPatchData={"Boot": bootPatchData}
                rc=self.rfr.backend.systems.doPatch(systemid, reqPatchData)

            elif prop in self.systemsVolatileDict[systemid]:
                self.systemsVolatileDict[systemid][prop]=patchData[prop]
                reqPatchData={ prop: patchData[prop] }
                rc=self.rfr.backend.systems.doPatch(systemid, reqPatchData)

            elif prop in self.systemsDb[systemid]:
                self.systemsDb[systemid][prop]=patchData[prop]
                reqPatchData={ prop: patchData[prop] }
                rc=self.rfr.backend.systems.doPatch(systemid, reqPatchData)
                updateSystemsDb=True
            else:
                pass

        if updateSystemsDb is True:
            self.updateStaticSystemsDbFile()

        # update volatile struct with patch time
        curTime=datetime.datetime.utcnow()
        self.systemsVolatileDict[systemid]["UpdateTime"]=curTime

        return(0, 204, "", "", hdrs)



    # **make calls to Backend to update the resourceDb and resourceVolatileDict
    # The first--if we havent already, get staticDiscoverySystemsInfo
    def updateResourceDbsFromBackend(self, systemid):
        if( (not "GotStaticDiscoveryInfo" in self.systemsVolatileDict[systemid]) or
        (self.systemsVolatileDict[systemid]["GotStaticDiscoveryInfo"] is False )):
            self.rfr.logMsg("DEBUG","--------SystemsFrontEnd: calling backend.systems.updateREsourceDbs()")
            updateStaticProps=True;
        else:
            # just update statics one time
            updateStaticProps=False;
            
        rc,resp=self.rfr.backend.systems.updateResourceDbs(systemid, updateStaticProps=updateStaticProps)
        if( rc==0):
            # set flag we have discovered staticDiscovery data
            self.systemsVolatileDict[systemid]["GotStaticDiscoveryInfo"]=True
        else:
            self.rfr.logMsg("ERROR","systems.updateResourceDbsFromBackend(): Error from Backend Updating ResourceDBs: rc={}".format(rc))
        return(rc)



    # GET VOLATILE PROPERTIES
    # get the volatile properties that were assigned when the resource was created
    #    volatileProperties = the list of properties that the service treats as volatile
    #    resourceDb=the non-volatile resource database dict
    #    volatileDict=the volatile resource dict
    #  return dict of properties to add to the output
    #  usage:  
    #     volatileProps = getVolatileProperties(volatileProperties,resourceDb,volatileDict):
    #     for prop in volatileProps:
    #         response[prop] = volatileProps[prop]
    def getVolatileProperties(self,volatileProperties,resId,sensorId,resourceDb,volatileDict):
        data={}
        # only include properties that are in the service volatileProperties list
        if resId is not None:
            for prop in volatileProperties:
                # if the property was also included in the database "Volatile" list
                if prop in resourceDb[resId][sensorId]["Volatile"]:
                    # if the property is in the volatile dict, then use that 
                    if (resId in volatileDict) and ( sensorId in volatileDict[resId]) and (prop in volatileDict[resId][sensorId]):
                        data[prop]=volatileDict[resId][sensorId][prop]
                    # else, if the prop was assigned a default value in Db, then use that
                    elif prop in resourceDb[resId][sensorId]:
                        data[prop]=resourceDb[resId][sensorId][prop]
                    else:
                        # the prop is a volatile prop, but there is no value in the volatile dict
                        # and there is no default in the database, so set to None which will map to Json null in response
                        data[prop]=None
                # else: case where the property is not part of the volatile list in the db for this resource
                else:
                    # if the prop itself is in the Db, then treat it as non-volatile and use value in the db
                    if prop in resourceDb[resId][sensorId]:
                        data[prop]=resourceDb[resId][sensorId][prop]
        else:
            for prop in volatileProperties:
                # if the property was also included in the database "Volatile" list
                if ("Volatile" in resourceDb) and (prop in resourceDb["Volatile"]):
                    # if the property is in the volatile dict, then use that 
                    if prop in volatileDict:
                        data[prop]=volatileDict[prop]
                    # else, if the prop was assigned a default value in Db, then use that
                    elif prop in resourceDb:
                        data[prop]=resourceDb[prop]
                    else:
                        # the prop is a volatile prop, but there is no value in the volatile dict
                        # and there is no default in the database, so set to None which will map to Json null in response
                        data[prop]=None
                # else: case where the property is not part of the volatile list in the db for this resource
                else:
                    # if the prop itself is in the Db, then treat it as non-volatile and use value in the db
                    if prop in resourceDb:
                        data[prop]=resourceDb[prop]

        return(data)


    # GET STATUS PROPERTIES
    #    statusSubProps  = the list of status sub-properties that this redfish service supports
    #    resourceDb=the non-volatile resource database dict
    #    volatileDict=the volatile resource dict
    #  return: dict of properties to add to the output
    # Usage example for systemsEntry:
    #    statusProps = getStatusProperties(statusSubProps, self.systemsDb[systemid],self.systemsVolatileDict[systemid]
    #
    def getStatusProperties(self,statusSubProps, resId, sensorId, resourceDb, volatileDict):
        # set the status properties
        resp={}
        if resId is not None:
            if "Status" in resourceDb[resId][sensorId]:
                for subProp in statusSubProps:
                    if subProp in resourceDb[resId][sensorId]["Status"]:
                        # if the volatile resource struct has captured the value, get it from there 
                        if (resId in volatileDict) and ( sensorId in volatileDict[resId]) and ("Status" in volatileDict[resId][sensorId]):
                            if subProp in volatileDict[resId][sensorId]["Status"]:
                                if "Status" not in resp:
                                     resp["Status"]={}
                                resp["Status"][subProp] = volatileDict[resId][sensorId]["Status"][subProp]
                            else:
                                if "Status" not in resp:
                                    resp["Status"]={}
                                resp["Status"][subProp] = resourceDb[resId][sensorId]["Status"][subProp]
                        else:
                            if "Status" not in resp:
                                resp["Status"]={}
                            resp["Status"][subProp] = resourceDb[resId][sensorId]["Status"][subProp]
        else:
            if "Status" in resourceDb:
                for subProp in statusSubProps:
                    if subProp in resourceDb["Status"]:
                        # if the volatile resource struct has captured the value, get it from there 
                        if "Status" in volatileDict:
                            if subProp in volatileDict["Status"]:
                                if "Status" not in resp:
                                    resp["Status"]={}
                                resp["Status"][subProp] = volatileDict["Status"][subProp]
                        else:
                            if "Status" not in resp:
                                resp["Status"]={}
                            resp["Status"][subProp] = resourceDb["Status"][subProp]
        return(resp)





    # POST System Reset  -- Reset System
    def resetSystem(self, request, systemid, resetData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the systemid is valid
        if systemid not in self.systemsDb:
            return(4, 404, "Not Found","", hdrs)

        #  if there is no ResetAllowable value property in systemsDb, then the system doesn't support reset
        if "ActionsResetAllowableValues" not in self.systemsDb[systemid]:
            return(4, 404, "Not Found","", hdrs)

        # verify all the required properties were sent in the request
        if "ResetType" not in resetData: 
            return(4,400,"Required  request property not included in request","",hdrs)
        else:
            # get the resetValue
            resetValue=resetData["ResetType"]

        # check if this is a valid resetType for Redfish xg88-TODO-need to review if list has changed
        redfishValidResetValues=["On","ForceOff","GracefulShutdown","GracefulRestart","ForceRestart",
                                 "Nmi","ForceOn","PushPowerButton","PowerCycle"]
        if resetValue not in redfishValidResetValues:
            return(4,400,"invalid resetType","", hdrs)

        # check if this is a resetType that this system does not support
        if resetValue not in self.systemsDb[systemid]["ActionsResetAllowableValues"]:
            return(4,400,"invalid resetType","", hdrs)

        # if here we have a valid request and valid resetValue 
        # send request to reset system to backend
        self.rfr.logMsg("DEBUG","--------SystemsFrontEnd: called backend.doSystemReset()ResetType: {}".format(resetValue))
        rc=self.rfr.backend.systems.doSystemReset(systemid,resetValue)

        if( rc==0):
            return(0, 204, "SUCCESS", "", hdrs)
        elif( rc == 400):
            return(4,400,"invalid resetType","", hdrs)
        else:
            return(rc,500, "ERROR executing backend doSystemReset. rc={}".format(rc),"", hdrs)

        # DONE


    # GET System Processor Collection
    def getSystemProcessorCollection(self, request, sysid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "Processors" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else:
            notFound=False
        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.processorsCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # **make calls to Backend to update the resourceDb 
        #   the backend will query the node if the processorsDb is not known or up to date
        rc=self.rfr.backend.systems.updateProcessorsDbFromBackend(sysid, noCache=False)
        #xg rc,resp=self.rfr.backend.systems.updateResourceDbs(systemid, updateStaticProps=updateStaticProps)
        #xg99999
        if( rc != 0):
            errMsg="ERROR updating Processor Collection info from backend. rc={}".format(rc)
            self.rfr.logMsg("ERROR",errMsg)
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(9, 500, errMsg, "", errhdrs)

        # first just copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.processorsCollectionTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/Processors"
        responseData2["@odata.id"] = odataId
        uriBase = odataId + "/"

        count=0
        # now walk through the entries in the processorsDb and build the Members array
        # note that the members array is an empty array in the template
        if sysid in self.processorsDb and "Id" in self.processorsDb[sysid]:
            for procid in self.processorsDb[sysid]["Id"]:
                # increment members count, and create the member for the next entry
                count=count+1
                memberUri=uriBase + procid
                newMember=[{"@odata.id": memberUri}]

                # add the new member to the members array we are building
                responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)

    def stubResponse(self):
        rc=1
        statusCode=501
        errString="Not Implemented--Work In Progress"
        resp=""
        hdrs={}
        return(rc,statusCode,errString,resp,hdrs)
        
    # xg9988
    # GET System Memory Collection
    def getSystemMemoryCollection(self, request, sysid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "Memory" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else:
            notFound=False
        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.memoryCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # **make calls to Backend to update the resourceDb 
        #   the backend will query the node if the memoryDb is not known or up to date
        rc=self.rfr.backend.systems.updateMemoryDbFromBackend(sysid, noCache=False)
        if( rc != 0):
            errMsg="ERROR updating Memory Collection info from backend. rc={}".format(rc)
            self.rfr.logMsg("ERROR",errMsg)
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(9, 500, errMsg, "", errhdrs)

        # first just copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.memoryCollectionTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/Memory"
        responseData2["@odata.id"] = odataId
        uriBase = odataId + "/"

        count=0
        # now walk through the entries in the memoryDb and build the Members array
        # note that the members array is an empty array in the template
        if sysid in self.memoryDb and "Id" in self.memoryDb[sysid]:
            for memid in self.memoryDb[sysid]["Id"]:
                # increment members count, and create the member for the next entry
                count=count+1
                memberUri=uriBase + memid
                newMember=[{"@odata.id": memberUri}]

                # add the new member to the members array we are building
                responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)



    # GET System SimpleStorage Collection
    def getSystemSimpleStorageCollection(self, request, sysid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "SimpleStorage" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else:
            notFound=False
        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.simpleStorageCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # **make calls to Backend to update the resourceDb 
        #   the backend will query the node if the simpleStorageDb is not known or up to date
        rc=self.rfr.backend.systems.updateSimpleStorageDbFromBackend(sysid, noCache=False)
        if( rc != 0):
            errMsg="ERROR updating SimpleStorage Collection info from backend. rc={}".format(rc)
            self.rfr.logMsg("ERROR",errMsg)
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(9, 500, errMsg, "", errhdrs)

        # first just copy the template resource and update odata.id since it is a funct of cntlrid
        responseData2=dict(self.simpleStorageCollectionTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/SimpleStorage"
        responseData2["@odata.id"] = odataId
        uriBase = odataId + "/"

        count=0
        # now walk through the entries in the simpleStorageDb and build the Members array
        # note that the members array is an empty array in the template
        if sysid in self.simpleStorageDb and "Id" in self.simpleStorageDb[sysid]:
            for cntlrid in self.simpleStorageDb[sysid]["Id"]:
                # increment members count, and create the member for the next entry
                count=count+1
                memberUri=uriBase + cntlrid
                newMember=[{"@odata.id": memberUri}]

                # add the new member to the members array we are building
                responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)



    # GET System EthernetInterface Collection
    def getSystemEthernetInterfaceCollection(self, request, sysid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "EthernetInterfaces" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else:
            notFound=False
        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.ethernetInterfaceCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # **make calls to Backend to update the resourceDb 
        #   the backend will query the node if the ethernetInterfaceDb is not known or up to date
        rc=self.rfr.backend.systems.updateEthernetInterfaceDbFromBackend(sysid, noCache=False)
        if( rc != 0):
            errMsg="ERROR updating EthernetEnterface Collection info from backend. rc={}".format(rc)
            self.rfr.logMsg("ERROR",errMsg)
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(9, 500, errMsg, "", errhdrs)

        # first just copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.ethernetInterfaceCollectionTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/EthernetInterfaces"
        responseData2["@odata.id"] = odataId
        uriBase = odataId + "/"

        count=0
        # now walk through the entries in the processorsDb and build the Members array
        # note that the members array is an empty array in the template
        if sysid in self.ethernetInterfaceDb and "Id" in self.ethernetInterfaceDb[sysid]:
            for ethid in self.ethernetInterfaceDb[sysid]["Id"]:
                # increment members count, and create the member for the next entry
                count=count+1
                memberUri=uriBase + ethid
                newMember=[{"@odata.id": memberUri}]

                # add the new member to the members array we are building
                responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)




    #xg9988
    # GET System Processor Entry
    def getSystemProcessorEntry(self, request, sysid, procid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "Processors" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else: 
            # **make calls to Backend to update the resourceDb 
            #   the backend will query the node if the processorsDb is not up to date
            rc=self.rfr.backend.systems.updateProcessorsDbFromBackend(sysid, noCache=False, procid=procid)
            if( rc != 0):
                errMsg="ERROR updating Processor info from backend. rc={}".format(rc)
                self.rfr.logMsg("ERROR",errMsg)
                errhdrs=self.hdrs.rfRespHeaders(request)
                return(9, 500, errMsg, "", errhdrs)
            # verify the the procid is valid
            if sysid not in self.processorsDb or "Id" not in self.processorsDb[sysid]:
                notFound=True
            elif procid not in self.processorsDb[sysid]["Id"]:
                notFound=True
            else:
                thisDbEntry = self.processorsDb[sysid]["Id"][procid]
                notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.processorEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        procStringProperties=["Name","Socket","ProcessorType","Manufacturer","Model","MaxSpeedMHz","TotalCores",
                        "TotalThreads", "ProcessorId" ]
        procArrayProperties=["ProcessorArchitecture", "InstructionSet" ]

        # xg99: Issues re iDrac14G: Model="", 
        # xg99:     ProcessorArchitecture=[ { "Member": "x86" } ]
        # xg99:     InstructionSet=[ { "Member": "x86-64" } ]

        # copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.processorEntryTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/Processors/" + procid
        responseData2["@odata.id"] = odataId
        responseData2["Id"] = procid
        responseData2["Description"] = "The properties of a Processor attached to this System"
 
        # get the base string properties
        for prop in procStringProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]
        # get the proc array properties---output as base enums
        for prop in procArrayProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]
        # get the Intel RackScale OEM properties
        if "OemIntelRsd" in thisDbEntry:
            responseData2["Oem"] = {}
            responseData2["Oem"]["Intel_RackScale"] = {"@odata.type": "#Intel.Oem.Processor"}
            for prop2 in thisDbEntry["OemIntelRsd"]:
                responseData2["Oem"]["Intel_RackScale"][prop2]=thisDbEntry["OemIntelRsd"][prop2]
        # get status properties
        if "Status" in thisDbEntry:
            responseData2["Status"]=thisDbEntry["Status"]

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)
        #xg9988


    # GET System Memory Entry
    def getSystemMemoryEntry(self, request, sysid, memid):
        # verify that the systemid and memid is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "Memory" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else: 
            # **make calls to Backend to update the resourceDb 
            #   the backend will query the node if the memoryDb if not up to date
            rc=self.rfr.backend.systems.updateMemoryDbFromBackend(sysid, noCache=False, memid=memid)
            if( rc != 0):
                errMsg="ERROR updating Memory info from backend. rc={}".format(rc)
                self.rfr.logMsg("ERROR",errMsg)
                errhdrs=self.hdrs.rfRespHeaders(request)
                return(9, 500, errMsg, "", errhdrs)
            # verify the the memid is valid
            if sysid not in self.memoryDb or "Id" not in self.memoryDb[sysid]:
                notFound=True
            elif memid not in self.memoryDb[sysid]["Id"]:
                notFound=True
            else:
                thisDbEntry = self.memoryDb[sysid]["Id"][memid]
                notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.memoryEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        memStringProperties=["Name", "DeviceLocator", "SerialNumber","MemoryType",
                              "OperatingSpeedMhz","DataWidthBits","ErrorCorrection",
                              "BaseModuleType","CapacityMiB","BusWidthBits","Manufacturer",
                              "PartNumber","MemoryDeviceType", "RankCount","MemoryMedia","AllowedSpeedsMhz"
                              "FirmwareRevision","FirmwareApiVersion","FunctionClasses","VendorID","DeviceId",
                              "SubsystemVendorID","SubsystemDeviceID","MaxTDPMilliWatts","SecurityCapabilities",
                              "SpareDeviceCount","MemoryLocation","VolatileRegionSizeLimitMiB","PersistentRegionSizeLimitMiB"
                              "Regions","OperatingMemoryModes","PowerManagementPolicy","IsSpareDeviceEnabled",
                              "IsRankSpareEnabled" ]
        # TODO add "Metrics" collection and Actions

        # copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.memoryEntryTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/Memory/" + memid
        responseData2["@odata.id"] = odataId
        responseData2["Id"] = memid
        responseData2["Description"] = "The Memory Inventory Information for the ComputerSystem"
 
        # get the base string properties
        for prop in memStringProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]
        # get status properties
        if "Status" in thisDbEntry:
            responseData2["Status"]=thisDbEntry["Status"]

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)


    # GET System SimpleStorage Entry
    def getSystemSimpleStorageEntry(self, request, sysid, cntlrid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "SimpleStorage" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else: 
            # **make calls to Backend to update the resourceDb 
            #   the backend will query the node if the simpleStorageDb is not up to date
            rc=self.rfr.backend.systems.updateSimpleStorageDbFromBackend(sysid, noCache=False, cntlrid=cntlrid)
            if( rc != 0):
                errMsg="ERROR updating SimpleStorage info from backend. rc={}".format(rc)
                self.rfr.logMsg("ERROR",errMsg)
                errhdrs=self.hdrs.rfRespHeaders(request)
                return(9, 500, errMsg, "", errhdrs)
            # verify that the cntlrid is valid
            if sysid not in self.simpleStorageDb or "Id" not in self.simpleStorageDb[sysid]:
                notFound=True
            elif cntlrid not in self.simpleStorageDb[sysid]["Id"]:
                notFound=True
            else:
                thisDbEntry = self.simpleStorageDb[sysid]["Id"][cntlrid]
                notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.simpleStorageEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        simpleStorageStringProperties=["Name", "UefiDevicePath" ]
        devicesProperties=["Name", "Manufacturer", "Model", "CapacityBytes", "Status"]

        # copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.simpleStorageEntryTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/SimpleStorage/" + cntlrid
        responseData2["@odata.id"] = odataId
        responseData2["Id"] = cntlrid
        responseData2["Description"] = "The Storage Controller properties and attached drive info"
 
        # get the base string properties
        for prop in simpleStorageStringProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]
        # get the Device properties
        responseDeviceList=[]       
        if "Devices" in thisDbEntry:
            deviceCount=0
            for device in thisDbEntry["Devices"]:
                #thisDevice=thisDbEntry["Devices"][device]
                responseThisDeviceEntry=dict()
                for deviceProp in devicesProperties:
                    if deviceProp in device:
                        responseThisDeviceEntry[deviceProp] = device[deviceProp]
                responseDeviceList.append(responseThisDeviceEntry)
                deviceCount = deviceCount + 1
        responseData2["Devices"] = responseDeviceList
        responseData2["Devices@odata.count"]=deviceCount

        # get status properties
        if "Status" in thisDbEntry:
            responseData2["Status"]=thisDbEntry["Status"]

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)


    # GET System EthernetInterface Entry
    def getSystemEthernetInterfaceEntry(self, request, sysid, ethid):
        # verify that the systemid and procId is valid
        if sysid not in self.systemsDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.systemsDb[sysid]:
            notFound=True
        elif "EthernetInterfaces" not in self.systemsDb[sysid]["BaseNavigationProperties"]:
            notFound=True
        else: 
            # **make calls to Backend to update the resourceDb 
            #   the backend will query the node if the EthernetInterfaceDb is not up to date
            rc=self.rfr.backend.systems.updateEthernetInterfaceDbFromBackend(sysid, noCache=False, ethid=ethid)
            if( rc != 0):
                errMsg="ERROR updating System EthernetInterface info from backend. rc={}".format(rc)
                self.rfr.logMsg("ERROR",errMsg)
                errhdrs=self.hdrs.rfRespHeaders(request)
                return(9, 500, errMsg, "", errhdrs)
            # verify the the procid is valid
            if sysid not in self.ethernetInterfaceDb or "Id" not in self.ethernetInterfaceDb[sysid]:
                notFound=True
            elif ethid not in self.ethernetInterfaceDb[sysid]["Id"]:
                notFound=True
            else:
                thisDbEntry = self.ethernetInterfaceDb[sysid]["Id"][ethid]
                notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.ethernetInterfaceEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        #ethStringProperties=["Name", "MACAddress", "PermanentMACAddress" ]
        ethStringProperties=["Name", "UefiDevicePath", "Status", "InterfaceEnabled", "PermanentMACAddress", 
                "MACAddress", "SpeedMbps", "AutoNeg", "FullDuplex", "MTUSize", "HostName", "FQDN", 
                "MaxIPv6StaticAddresses", "VLAN", "IPv4Addresses", "IPv6Addresses", "IPv6StaticAddresses", 
                "IPv6AddressPolicyTable","IPv6DefaultGateway","NameServers" ]

        ethNavProperties=["VLANs"]

        # copy the template resource and update odata.id since it is a funct of sysid
        responseData2=dict(self.ethernetInterfaceEntryTemplate)
        odataId = "/redfish/v1/Systems/" + sysid + "/EthernetInterfaces/" + ethid
        responseData2["@odata.id"] = odataId
        responseData2["Id"] = ethid
        responseData2["Description"] = "The properties for a Computer System Ethernet Interface"
 
        # get the base string properties
        for prop in ethStringProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]
        # get status properties
        if "Status" in thisDbEntry:
            responseData2["Status"]=thisDbEntry["Status"]
        # get the eth Nav Properties (eg VLANs)
        for prop in ethNavProperties:
            if prop in thisDbEntry:
                ethNavProp={ "@odata.id": odataId + "/" + prop }
                responseData2[prop] = ethNavProp

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)




    # ------------------------------------------------------------

