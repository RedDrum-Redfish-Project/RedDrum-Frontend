
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys
import datetime
import copy
from  .redfish_headers import RfAddHeaders


class RfChassisResource():       
    # Class for all resources under /redfish/v1/Chassis
    # Note that this resource was created in serviceRoot for the Chassis Resource.
    def __init__(self,rfr ):
        self.rfr=rfr
        #xggx self.dellG5OemUtils=Dell_Dss9000_OemUtils(rfr)
        self.chassisDbDiscovered=None
        self.loadResourceTemplates(rfr )
        self.loadChassisDbFiles(rfr)
        sys.stdout.flush()
        self.hdrs=RfAddHeaders(rfr)

        self.staticProperties=["Name", "Description", "ChassisType", "Manufacturer", "Model", "SKU", "SerialNumber", "PartNumber",
             "Location" ]
        self.nonVolatileProperties=[ "AssetTag" ]
        self.temperatureStaticProperties=["Name", "SensorNumber", "UpperThresholdNonCritical", "UpperThresholdCritical", 
             "UpperThresholdFatal", "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", 
             "MinReadingRangeTemp", "MaxReadingRangeTemp", "PhysicalContext"  ]
        self.temperatureNonVolatileProperties=[]
        self.fansStaticProperties=["Name", "UpperThresholdNonCritical", "UpperThresholdCritical", "UpperThresholdFatal", 
             "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", "MinReadingRange", 
             "MaxReadingRange", "PhysicalContext", "RelatedItem", "Manufacturer", "Model","SerialNumber",
             "PartNumber","SparePartNumber", "ReadingUnits" ]
        self.fansNonVolatileProperties=[]
        self.voltagesStaticProperties=["Name", "SensorNumber", "UpperThresholdNonCritical", "UpperThresholdCritical", 
             "UpperThresholdFatal", "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", 
             "MinReadingRange", "MaxReadingRange", "PhysicalContext"  ]
        self.voltagesNonVolatileProperties=[]
        self.powerControlStaticProperties=["Name","PhysicalContext" ]
        self.powerControlPowerLimitNonVolatileProperties=["LimitInWatts", "LimitException", "CorrectionInMs" ]
        self.powerControlVolatileProperties=[ "PowerConsumedWatts" ]
        self.powerControlNonVolatileProperties=[ "PowerAllocatedWatts","PowerRequestedWatts","PowerCapacityWatts",
            "PowerAvailableWatts","PowerMetrics" ]
        self.psusStaticProperties=["Name"]
        self.psusNonVolatileProperties=["PowerSupplyType", "LineInputVoltageType", "PowerCapacityWatts", 
            "Manufacturer", "Model","SerialNumber","FirmwareVersion", "PartNumber","SparePartNumber"  ]
        self.magic="123456"

    def loadResourceTemplates( self, rfr ):
        # these are very bare-bones templates but we want to be able to update the resource version or context easily
        #   so the approach is to always start with a standard template for each resource type

        #load ChassisCollection Template
        self.chassisCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ChassisCollection.json")

        #load ChassisEntry Template
        self.chassisEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Chassis.json")

        #load ChassisPower Template
        self.chassisPowerTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Power.json")

        #load ChassisThermal Template
        self.chassisThermalTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Thermal.json")


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
            self.rfr.logMsg("CRITICAL","*****ERROR: Chassis Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
            sys.exit(10)
        

    def loadChassisDbFiles(self,rfr ):
        # if rfr.resourceDiscoveryUseDbCache is True:
        #   then if the chassis database files exist in /var/www/rf/chassisDb/* then load them to in-memory dict
        #        else if rfr.resourceDiscover=static, read static db files and save to the cache
        #        else,  kick-off job to discover the chassis data from the MC--may take 1-2 minutes, and save in cache
        # else, always run full discovery each time RM Redfish Service starats
        self.chassisDbDiscovered=False
        if rfr.useCachedDiscoveryDb is True:
            # first make sure all of the chassis DB files exist
            chassisDbCacheExists=True
            chasDbFiles=["ChassisDb.json", "FansDb.json", "TempSensorsDb.json", "PowerSuppliesDb.json", "VoltageSensorsDb.json", "PowerControlDb.json"]
            for filenm in chasDbFiles:
                chasDbFilePath=os.path.join(rfr.varDataPath,"chassisDb", filenm)
                if not os.path.isfile(chasDbFilePath):
                    chassisDbCacheExists = False
                    break
            # then load them into dictionaries
            if chassisDbCacheExists is True:
                self.chassisDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "ChassisDb.json") 
                self.fansDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "FansDb.json") 
                self.tempSensorsDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "TempSensorsDb.json") 
                self.powerSuppliesDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "PowerSuppliesDb.json") 
                self.voltageSensorsDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "VoltageSensorsDb.json") 
                self.powerControlDb=self.loadChassisDbFile(rfr.varDataPath, "chassisDb", "PowerControlDb.json") 
                self.chassisDbDiscovered=True

        return(0)

    # worker function to load CACHED chassis db file into dict
    def loadChassisDbFile( self, dataPath, subDir, filename ):
        filePath=os.path.join(dataPath, subDir, filename)
        if os.path.isfile(filePath):
            response=json.loads( open(filePath,"r").read() )
            return(response)
        else:
            self.rfr.logMsg("CRITICAL","*****ERROR: Chassis Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
            sys.exit(10)


    # clear the current Db Dicts and HDD caches
    def clearChassisResourceCaches(self,rfr):
        self.chassisDb=self.clearChassisDbFile(rfr, "chassisDb",  "ChassisDb.json") 
        self.fansDb=self.clearChassisDbFile(rfr, "chassisDb",  "FansDb.json") 
        self.tempSensorsDb=self.clearChassisDbFile(rfr, "chassisDb",  "TempSensorsDb.json") 
        self.powerSuppliesDb=self.clearChassisDbFile(rfr, "chassisDb",  "PowerSuppliesDb.json") 
        self.voltageSensorsDb=self.clearChassisDbFile(rfr, "chassisDb",  "VoltageSensorsDb.json") 
        self.powerControlDb=self.clearChassisDbFile(rfr, "chassisDb",  "PowerControlDb.json") 
        self.chassisDbDiscovered=False

    # worker function for above clear chassis resource caches 
    def clearChassisDbFile( self, rfr, subDir, filename ):
        clearedDb=dict()
        varDbFilePath=os.path.join(rfr.varDataPath, subDir, filename)
        #jsonEmptyDb=json.dumps(clearedDb,indent=4)
        #with open( varDbFilePath, 'w', encoding='utf-8') as f:
        #        f.write(jsonEmptyDb)
        if os.path.exists(varDbFilePath):
            os.remove(varDbFilePath)
        return(clearedDb)

    # functions to save the chassis Db dicts to their persistent files
    def updateStaticChassisDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.chassisDb,"ChassisDb.json")
        return(rc)

    def updateStaticPowerControlDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.powerControlDb,"PowerControlDb.json")
        return(rc)

    def updateStaticTempSensorDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.tempSensorsDb,"TempSensorsDb.json")
        return(rc)

    def updateStaticFansDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.fansDb,"FansDb.json") 
        return(rc)

    def updateStaticPowerSuppliesDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.powerSuppliesDb, "PowerSuppliesDb.json") 
        return(rc)

    def updateStaticVoltageSensorsDbFile( self ):
        rc=self.updateStaticChassisDbResourceFile(self.voltageSensorsDb, "VoltageSensorsDb.json") 
        return(rc)

    # worker function to write the various chassis Db Dicts back to the persistant chassis db file caches
    def updateStaticChassisDbResourceFile(self, resDb, resDbFile):
        varDbFilePath=os.path.join(self.rfr.varDataPath, "chassisDb", resDbFile)
        responseJson=json.dumps(resDb, indent=4)
        with open( varDbFilePath, 'w', encoding='utf-8') as f:
            f.write(responseJson)
        return(0)


    def initializeChassisVolatileDict(self,rfr):
        # this is the in-memory dict of volatile chassis properties
        # the sessionsDict is an dict indexed by   sessionsDict[sessionId][<sessionParameters>]
        #   self.chassisVolatileDict[chassisid]= a subset of the volatile chassid properties
        #       subset of: volatileProperties=["IndicatorLED", "PowerState" ] and "Status"
        #       subset of: {"IndicatorLED": <led>, "PowerState": <ps>, "Status":{"State":<s>,"Health":<h>}} 
        self.chassisVolatileDict=dict()   #create an empty dict of Chassis entries
        self.fansVolatileDict=dict()   #create an empty dict of Fans  entries
        self.tempSensorsVolatileDict=dict()   #create an empty dict of TempSensors  entries
        self.powerSuppliesVolatileDict=dict()   #create an empty dict of powerSupply entries
        self.voltageSensorsVolatileDict=dict()   #create an empty dict of voltage sensor entries
        self.powerControlVolatileDict=dict()   #create an empty dict of Power Control 

        # initialize the Volatile Dicts
        for chassisid in self.chassisDb:
            # inialize with empty members for all known chassis
            self.chassisVolatileDict[chassisid]={}
            self.fansVolatileDict[chassisid]={}
            self.tempSensorsVolatileDict[chassisid]={}
            self.powerSuppliesVolatileDict[chassisid]={}
            self.voltageSensorsVolatileDict[chassisid]={}
            self.powerControlVolatileDict[chassisid]={}


    # GET Chassis Collection
    def getChassisCollectionResource(self, request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.chassisCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # first copy the chassis Collection template 
        # then updates the Members array will each chassis previously discovered--in ChassisDb 

        # copy the chassisCollection template file (which has an empty roles array)
        responseData2=dict(self.chassisCollectionTemplate)
        count=0
        # now walk through the entries in the chassisDb and build the chassisCollection Members array
        # note that the members array is an empty array in the template
        uriBase="/redfish/v1/Chassis/"
        for chassisid in self.chassisDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=uriBase + chassisid
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)



    # GET Chassis Entry
    def getChassisEntry(self, request, chassisid):
        # generate error header for 4xx errors
        errhdrs=self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
                return(4, 404, "Not Found","",errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="GetPatch",
                                     resource=self.chassisEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.chassisEntryTemplate)

        # setup some variables to build response from
        basePath="/redfish/v1/Chassis/"
        #self.staticProperties=["Name", "Description", "ChassisType", "Manufacturer", "Model", "SKU", "SerialNumber", "PartNumber"]
        #self.nonVolatileProperties=[ "AssetTag" ]
        volatileProperties=[ "IndicatorLED", "PowerState", "PhysicalSecurity"]
        baseNavProperties=["LogServices", "Thermal", "Power"]
        statusSubProperties=["State", "Health", "HealthRollup"]
        linkNavProperties=["Contains", "ContainedBy", "PoweredBy", "CooledBy", "ManagedBy", "ComputerSystems", "ManagersInChassis"]

        # assign the required properties
        responseData2["@odata.id"] = basePath + chassisid
        responseData2["Id"] = chassisid

        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        rc=self.updateResourceDbsFromBackend(chassisid)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getChassisEntry(): updateResourceDbsFromBackend() returned error ")
            return(9, 500, "Internal Error", "", errhdrs)

        # set the base static properties that were assigned when the resource was created
        for prop in self.staticProperties:
            if prop in self.chassisDb[chassisid]:
                responseData2[prop] = self.chassisDb[chassisid][prop]

        # get the base non-volatile properties that were assigned when the resource was created
        # these are stored in the persistent cache but are not static--ex is assetTag
        for prop in self.nonVolatileProperties:
            if prop in self.chassisDb[chassisid]:
                responseData2[prop] = self.chassisDb[chassisid][prop]

        # get the volatile properties eg powerState
        volatileProps = self.getVolatileProperties(volatileProperties, None, None,
                        self.chassisDb[chassisid], self.chassisVolatileDict[chassisid])
        for prop in volatileProps:
            responseData2[prop] = volatileProps[prop]

        # get the status properties
        statusProps = self.getStatusProperties(statusSubProperties, None, None,
                      self.chassisDb[chassisid], self.chassisVolatileDict[chassisid])
        for prop in statusProps:
            responseData2[prop] = statusProps[prop]


        # set the base navigation properties:   /redfish/v1/Chassis/<baseNavProp>
        for prop in baseNavProperties:
            if "BaseNavigationProperties"  in  self.chassisDb[chassisid]:
                if prop in self.chassisDb[chassisid]["BaseNavigationProperties"]:
                    responseData2[prop] = { "@odata.id": basePath + chassisid + "/" + prop }


        # build the Actions data
        if "ActionsResetAllowableValues" in self.chassisDb[chassisid]:
            resetAction = { "target": basePath + chassisid + "/Actions/Chassis.Reset",
                            "ResetType@Redfish.AllowableValues": self.chassisDb[chassisid]["ActionsResetAllowableValues"] }
            if "Actions" not in responseData2:
                responseData2["Actions"]={}
            responseData2["Actions"]["#Chassis.Reset"]= resetAction

        if "ActionsOemSledReseat" in self.chassisDb[chassisid]:
            if self.chassisDb[chassisid]["ActionsOemSledReseat"] is True:
                resetAction = { "target": basePath + chassisid + "/Actions/Chassis.Reseat" }
                if "Actions" not in responseData2:
                    responseData2["Actions"]={}
                if "Oem" not in responseData2["Actions"]:
                    responseData2["Actions"]["Oem"]={}
                responseData2["Actions"]["Oem"]["#Dell.G5SledReseat"]= resetAction

        # build Dell OEM Section (Sleds only)
        if "Oem" in self.chassisDb[chassisid]:
            # define the legal oem properties
            oemDellG5NonVolatileProps = [ "SledType", "ParentSled", "SysIdForJbodSled" ]

            # check if each of the legal oem subProps are in the db
            oemData={}
            for prop in oemDellG5NonVolatileProps:
                if prop in self.chassisDb[chassisid]["Oem"]:
                    # since these sub-props are nonVolatile, read them from the database
                    oemData[prop] = self.chassisDb[chassisid]["Oem"][prop]
            if "Oem" not in responseData2:
                responseData2["Oem"]={}
            responseData2["Oem"]["Dell_G5MC"] = oemData

        # build Intel Rackscale OEM Section 
        if "hasOemRackScaleLocation" in self.chassisDb[chassisid]:
            if self.chassisDb[chassisid]["hasOemRackScaleLocation"] is True:
                locationId, parentId = self.rfr.backend.oemUtils.rsdLocation(chassisid)
                oemData = {"@odata.type": "#Intel.Oem.Chassis",
                           "Location": { "Id": locationId } }
                if parentId is not None:
                    oemData["Location"]["ParentId"]=parentId 
                if "Oem" not in responseData2:
                    responseData2["Oem"]={}
                responseData2["Oem"]["Intel_RackScale"] = oemData


        # build the navigation properties under Links : "Contains", "ContainedBy", ManagersIn...
        responseData2["Links"]={}
        for navProp in linkNavProperties:
            if navProp in self.chassisDb[chassisid]:
                #first do single entry nav properties
                if( navProp == "ContainedBy" ):
                    member= { "@odata.id": basePath + self.chassisDb[chassisid][navProp] }
                    responseData2["Links"][navProp] = member
                #otherwise, handle an array or list of nav properties
                else: 
                    pathSuffix=""  
                    if( (navProp == "ManagedBy") or (navProp == "ManagersInChassis") ):
                        linkBasePath="/redfish/v1/Managers/"
                    elif( navProp == "ComputerSystems") :
                        linkBasePath="/redfish/v1/Systems/"
                    else: # it is the /redfishg/v1/Chassis/
                        #linkBasePath=basePath
                        linkBasePath="/redfish/v1/Chassis/"
                        if navProp == "PoweredBy":  
                            pathSuffix="/Power"     
                        elif navProp == "CooledBy": 
                            pathSuffix="/Thermal"   
                        else:                       
                            pass                    

                    #start with an empty array
                    members = list()
                    # now create the array of members for this navProp
                    for memberId in self.chassisDb[chassisid][navProp]:
                        newMember= { "@odata.id": linkBasePath + memberId + pathSuffix}
                        #members = members + newMember
                        members.append(newMember)
                    # now add the members array to the response data
                    responseData2["Links"][navProp] = members

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "SUCCESS", jsonRespData2, respHdrs)



    # PATCH Chassis Entry
    def patchChassisEntry(self, request, chassisid, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
            return(4,404, "Not Found","", hdrs)

        #define the patchable properties in Chassis Resource
        patchableInRedfish=["AssetTag","IndicatorLED"]

        #first verify client didn't send us a property we cant patch based on Redfish Schemas
        for prop in patchData:
            if prop not in patchableInRedfish: 
                return(4,400, "Bad Request. Property: {} not patachable per Redfish Spec".format(prop),"", hdrs)

        #second check if this instance of chassis allows the patch data to be patched
        #  if there is no Patchable property in chassisDb, then nothing is patchable
        if "Patchable" not in self.chassisDb[chassisid]:
            return(4,400, "Bad Request. Resource is not patachable","", hdrs)

        # check if the specific property is patchable
        for prop in patchData:
            if prop not in self.chassisDb[chassisid]["Patchable"]:
                return(4,400, "Bad Request. Property: {} not patachable for this resource".format(prop),"", hdrs)

        # defensive chech for the setting data
        ledValidValues=["Lit", "Blinking", "Off"]
        if( prop=="IndicatorLED"):
            if patchData[prop] not in ledValidValues:
                return(4, 400, "Bad Request. Value: {} not valid for LED ".format(patchData[prop]),"", hdrs)

        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        #   this insures that the volDb is updated with all volatile properties
        rc=self.updateResourceDbsFromBackend(chassisid)
        if( rc != 0):
            self.rfr.logMsg("Error","patchChassisEntry(): updateResourceDbsFromBackend returned error ")
            return(5, 500, "Internal Error: Error getting resource Update from Backend", "", hdrs)

        # now construct the patch data, and update the volatileDict or resourceDb
        # send separate patches for each patch property, 
        updateChassisDb=False
        for prop in patchData:
            if prop in self.chassisVolatileDict[chassisid]:
                self.chassisVolatileDict[chassisid][prop]=patchData[prop]
                reqPatchData={ prop: patchData[prop]}
                rc=self.rfr.backend.chassis.doPatch(chassisid, reqPatchData)
            elif prop in self.chassisDb[chassisid]:
                # its a nonVolatile property.    Update it in chassisDb and update HDD cache
                self.chassisDb[chassisid][prop]=patchData[prop]
                reqPatchData={ prop: patchData[prop]}
                rc=self.rfr.backend.chassis.doPatch(chassisid, reqPatchData)
                updateChassisDb=True
            else:
                pass

        if updateChassisDb is True:
            self.updateStaticChassisDbFile()

        # update volatile struct with patch time
        curTime=datetime.datetime.utcnow()
        self.chassisVolatileDict[chassisid]["UpdateTime"]=curTime

        return(0, 204, "", "", hdrs)


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
    # Usage example for chassisEntry:
    #    statusProps = getStatusProperties(statusSubProps, self.chassisDb[chassisid],self.chassisVolatileDict[chassisid]
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


    # GET Thermal
    # Get Chassis Thermal  eg: GET /redfish/v1/Chassis/<chasid>/Thermal
    #  related structures
    #    self.fansDb
    #    self.tempSensorsDb
    #    self.fansVolatileDict[chassisid]
    #    self.tempSensorsVolatileDict[chassisid]
    def getChassisEntryThermal(self, request, chassisid):
        # generate headers
        errhdrs = self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
                return(4, 404, "Not Found","",errhdrs)

        if not "BaseNavigationProperties" in self.chassisDb[chassisid]:
                return(4, 404, "Not Found","",errhdrs)
        if not "Thermal" in self.chassisDb[chassisid]["BaseNavigationProperties"]:
                return(4, 404, "Not Found","",errhdrs)

        # generate headers
        respHdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.chassisThermalTemplate, allow="Get")

        # Process HEAD method
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.chassisThermalTemplate) 

        # setup some variables to build response from
        basePath="/redfish/v1/Chassis/"
        systemsBasePath="/redfish/v1/Systems/"

        # assign the required top-level properties
        responseData2["@odata.id"] = basePath + chassisid + "/Thermal"
        responseData2["Id"] = "Thermal"
        responseData2["Name"] = "Thermal"
        responseData2["Description"] = "Thermal Resource for the chassis (Fans, TempSensors)"

        # **make calls to Backend to update the "Thermal" resourceDb and resourceVolatileDict
        #   this includes:  self.tempSensorsDb[chassisid], self.tempSensorsVolatileDict[chassisid]
        #                   self.fansDb[chassisid],        self.fansVolatileDict[chassisid]
        rc=self.updateThermalResourceDbsFromBackend(chassisid)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getChassisEntryThermal(): updateThermalResourceDbsFromBackend() returned error ")
            return(9, 500, "Internal Error", "", errhdrs)

        # set temperature array variables to build response from
        # defined in init function
        #   self.temperatureStaticProperties=["Name", "SensorNumber", "UpperThresholdNonCritical", "UpperThresholdCritical", 
        #     "UpperThresholdFatal", "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", 
        #     "MinReadingRangeTemp", "MaxReadingRangeTemp", "PhysicalContext"  ]
        #   self.temperatureNonVolatileProperties=[]
        temperatureVolatileProperties=["ReadingCelsius" ]
        temperatureStatusSubProperties=["State", "Health"]

        # Add temperature sensors
        # if temperatureSensors in this chassis, add them
        if chassisid in self.tempSensorsDb:
            # set the base static properties that were assigned when the resource was created
            temperatureArray=list()
            if "Id" not in self.tempSensorsDb[chassisid]:
                self.tempSensorsDb[chassisid]={ "Id": {} }
            for sensorId in self.tempSensorsDb[chassisid]["Id"]:   # sensors "0", "1", ...
                sensorData={}

                # add the required Id and MemberId properties
                sensorData["@odata.id"] = basePath + chassisid + "/Thermal#/Temperatures/" + sensorId
                sensorData["MemberId"]  = sensorId

                # add the static properties
                for prop in self.temperatureStaticProperties:
                    if prop in self.tempSensorsDb[chassisid]["Id"][sensorId]:
                        sensorData[prop] = self.tempSensorsDb[chassisid]["Id"][sensorId][prop]

                # add the non-volatile properties -- xg currently empty for G5
                for prop in self.temperatureNonVolatileProperties:
                    if prop in self.tempSensorsDb[chassisid]["Id"][sensorId]:
                        sensorData[prop] = self.tempSensorsDb[chassisid]["Id"][sensorId][prop]

                # add the volatile properties that were assigned when the resource was created
                volatileProps = self.getVolatileProperties(temperatureVolatileProperties, "Id", sensorId,
                                      self.tempSensorsDb[chassisid], self.tempSensorsVolatileDict[chassisid])
                for prop in volatileProps:
                    sensorData[prop] = volatileProps[prop]

                # add the status properties 
                statusProps = self.getStatusProperties(temperatureStatusSubProperties, "Id", sensorId,
                                      self.tempSensorsDb[chassisid],
                                      self.tempSensorsVolatileDict[chassisid])
                for prop in statusProps:
                    sensorData[prop] = statusProps[prop]

                # Add Temp Sensor related-items 
                # The service will create relatedItems entries pointing to the related chassis and system
                #  based on the AddRelatedItems property in the Temp Db entry
                if "AddRelatedItems" in self.tempSensorsDb[chassisid]["Id"][sensorId]:
                    relatedItemMembers=list()
                    if "Chassis" in self.tempSensorsDb[chassisid]["Id"][sensorId]["AddRelatedItems"]:
                        relatedItemMember = {"@odata.id": basePath + chassisid }
                        relatedItemMembers.append(relatedItemMember)
                    if "System" in self.tempSensorsDb[chassisid]["Id"][sensorId]["AddRelatedItems"]:
                        if "ComputerSystems" in self.chassisDb[chassisid]:
                            sysid=self.chassisDb[chassisid]["ComputerSystems"]
                            if( len(sysid) > 0 ):
                                relatedItemMember = {"@odata.id": systemsBasePath + sysid[0] }
                                relatedItemMembers.append(relatedItemMember)
                        
                    # add the RelatedItem Property to the response
                    if( len(relatedItemMembers) > 0):
                        sensorData["RelatedItem"] = relatedItemMembers

                # add the Temperatures entry array to the Temperatures array
                temperatureArray.append(sensorData)

            # Add the new member to the Temperatures array
            if "Temperatures" not in responseData2:
                responseData2["Temperatures"]={}
            responseData2["Temperatures"] = temperatureArray

        # set fan array variables to build response from
        #  self.* properties initialized in init method
        #   self.fansStaticProperties=["Name", "UpperThresholdNonCritical", "UpperThresholdCritical", "UpperThresholdFatal", 
        #     "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", "MinReadingRange", 
        #     "MaxReadingRange", "PhysicalContext", "RelatedItem", "Manufacturer", "Model","SerialNumber",
        #     "PartNumber","SparePartNumber", "ReadingUnits" ]
        #   self.fansNonVolatileProperties=[]
        fansVolatileProperties=["Reading", "IndicatorLED" ]
        fansStatusSubProperties=["State", "Health"]

        # Create a resundancy set list to collect all of the fan redundancy group members for the fans
        redundancySetMembers=list()

        # add Fan Array properties
        if chassisid in self.fansDb:
            fanArray=list()
            if "Id" not in self.fansDb[chassisid]:
                self.fansDb[chassisid]={ "Id": {} }
           
            # set the base static properties that were assigned when the resource was created
            for fanId in self.fansDb[chassisid]["Id"]:   # fan "0", "1", ...
                sensorData={}

                # add the required Id and MemberId properties
                sensorData["@odata.id"] = basePath + chassisid + "/Thermal#/Fans/" + fanId
                sensorData["MemberId"]  = fanId

                # add the static properties
                for prop in self.fansStaticProperties:
                    if prop in self.fansDb[chassisid]["Id"][fanId]:
                        sensorData[prop] = self.fansDb[chassisid]["Id"][fanId][prop]

                # add the non-volatile properties -- initiall empty for G5
                for prop in self.fansNonVolatileProperties:
                    if prop in self.fansDb[chassisid]["Id"][fanId]:
                        sensorData[prop] = self.fansDb[chassisid]["Id"][fanId][prop]

                # add the volatile properties that were assigned when the resource was created
                volatileProps = self.getVolatileProperties(fansVolatileProperties, "Id", fanId,
                                      self.fansDb[chassisid],
                                      self.fansVolatileDict[chassisid])
                for prop in volatileProps:
                    sensorData[prop] = volatileProps[prop]

                # add the status properties 
                statusProps = self.getStatusProperties(fansStatusSubProperties, "Id", fanId,
                                      self.fansDb[chassisid],
                                      self.fansVolatileDict[chassisid])
                for prop in statusProps:
                    sensorData[prop] = statusProps[prop]

                # add fan self-generated properties 
                #  set depricated property FanName = same value as Name
                if "Name" in sensorData:
                    sensorData["FanName"]=sensorData["Name"]

                # Add Fan entry Redundancy information
                #  if the Fan entry in the fan database has a "RedundancyGroup" property,
                #  then the service will create one Redundancy member for the fan
                #  This member will point to a single redundancy group 
                if "RedundancyGroup" in self.fansDb[chassisid]["Id"][fanId]:
                    redundancyGroup = self.fansDb[chassisid]["Id"][fanId]["RedundancyGroup"]
                    # create the redundancy group member 
                    redundancyMember    = {"@odata.id": basePath + chassisid + "/Thermal#/Redundancy/" + redundancyGroup }
                    redundancySetMember = {"@odata.id": basePath + chassisid + "/Thermal#/Fans/" + fanId }

                    # add the member to the Redundancy array for this fan 
                    # note that the service only supports one redundancy group per fan
                    redundancyMembers=list()
                    redundancyMembers.append(redundancyMember)
                        
                    # add redundancyMembers to the fan data
                    sensorData["Redundancy"] = redundancyMembers

                    # Finally, add the redundancy group to the redundancySet array 
                    redundancySetMembers.append(redundancySetMember)

                fanArray.append(sensorData)

            # Add the new member to the Fan array
            if "Fans" not in responseData2:
                responseData2["Fans"]={}
            responseData2["Fans"] = fanArray

        # Add the redundancy group information
        #  remember we had earlier in the function created a redundancySetMembers=list()
        #  if this has any redundancy groups in it, we create the redundancy property
        if chassisid in self.fansDb:
            #if we collected any redundancy groups when building the Fans array, 
            # and we have a redundancy entry in the fan db entry for the chassis, then create the redundancy entry
            if( (len(redundancySetMembers) > 0) and ("RedundancyGroup" in self.fansDb[chassisid]) ):
                # define the list of redundancy properties
                redundancyProperties=["Name", "Mode", "MinNumNeeded", "MaxNumSupported"]
                fansRedundancyStatusSubProperties=["State", "Health"]

                redundancyArray=list()
                # set the base static properties for this redundancy group
                for redundancyGroup in self.fansDb[chassisid]["RedundancyGroup"]:
                    sensorData={}

                    # add the required Id and MemberId properties
                    sensorData["@odata.id"] = basePath + chassisid + "/Thermal#/Redundancy/" + redundancyGroup
                    sensorData["MemberId"]  = redundancyGroup
 
                    # add the standard redundancyProperty Properties that this service uses
                    for prop in redundancyProperties:
                        if prop in self.fansDb[chassisid]["RedundancyGroup"][redundancyGroup]:
                            sensorData[prop] = self.fansDb[chassisid]["RedundancyGroup"][redundancyGroup][prop]

                    # add the RedundancySet property
                    # note that when we created the fan entries, we built the redundancySetMembers array
                    # so all we have to do is add it to the property
                    sensorData["RedundancySet"] = redundancySetMembers

                    # add status to the redundancy array
                    # add the status properties 
                    statusProps = self.getStatusProperties(fansRedundancyStatusSubProperties, "RedundancyGroup", 
                                       redundancyGroup, self.fansDb[chassisid], self.fansVolatileDict[chassisid])
                    for prop in statusProps:
                        sensorData[prop] = statusProps[prop]

                redundancyArray.append(sensorData)

                # Add the new member to the Redundancy array
                if "Redundancy" not in responseData2:
                    responseData2["Redundancy"]={}
                responseData2["Redundancy"] = redundancyArray

        # completed creating response Data in responseData2 dict

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)


    # GET Power
    # Get Chassis Power 
    #  related structures
    #    self.powerSuppliesDb   from .../chassisDb/PowerSuppliesDb.json
    #    self.voltageSensorsDb  from .../chassisDb/VoltageSensorsDb.json
    #    self.powerControlDb    from .../chassisDb/PowerControlDb.json
    #    self.powerSuppliesVolatileDict
    #    self.voltageSensorsVolatileDict
    #    self.powerControlVolatileDict

    def getChassisEntryPower(self, request, chassisid):
        # generate headers
        errhdrs = self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
                return(4, 404, "Not Found","",errhdrs)

        if not "BaseNavigationProperties" in self.chassisDb[chassisid]:
                return(4, 404, "Not Found","",errhdrs)

        if not "Power" in self.chassisDb[chassisid]["BaseNavigationProperties"]:
                return(4, 404, "Not Found","",errhdrs)

        # generate headers
        # first find out if PowerControl is Patchable for this resource
        powerControlIsPatchable=False
        if chassisid in self.powerControlDb:
            if "Id" in self.powerControlDb[chassisid]:
                for powerControlId  in self.powerControlDb[chassisid]["Id"]:
                    if "Patchable" in self.powerControlDb[chassisid]["Id"][powerControlId]:
                        for prop in self.powerControlPowerLimitNonVolatileProperties:
                            if prop in self.powerControlDb[chassisid]["Id"][powerControlId]["Patchable"]:
                                powerControlIsPatchable=True
        if powerControlIsPatchable is True:
            allowableMethods="GetPatch"
        else:
            allowableMethods="Get"
        # then create the response headers
        respHdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.chassisPowerTemplate, allow=allowableMethods)

        # Process HEAD method
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.chassisPowerTemplate) 

        # setup some variables to build response from
        basePath="/redfish/v1/Chassis/"
        systemsBasePath="/redfish/v1/Systems/"

        # assign the required top-level properties
        responseData2["@odata.id"] = basePath + chassisid + "/Power"
        responseData2["Id"] = "Power"
        responseData2["Name"] = "Power"
        responseData2["Description"] = "Power Resource for Chassis (Voltage sensors, PowerSupplies, PowerControl)"

        # **make calls to Backend to update the "Power" resourceDb and resourceVolatileDict
        #   this includes:  self.voltageSensorsDb[chassisid], self.voltageSensorsVolatileDict[chassisid])
        #                   self.powerControlDb[chassisid],   self.powerControlVolatileDict[chassisid])
        #                   self.powerSuppliesDb[chassisid],  self.powerSuppliesVolatileDict[chassisid])
        rc=self.updatePowerResourceDbsFromBackend(chassisid)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getChassisEntryPower(): updatePowerResourceDbsFromBackend() returned error ")
            return(9, 500, "Internal Error", "",  errhdrs)

        # set Voltages array variables to build response from
        #  these initialized in init method
        #    self.voltagesStaticProperties=["Name", "SensorNumber", "UpperThresholdNonCritical", "UpperThresholdCritical", 
        #     "UpperThresholdFatal", "LowerThresholdNonCritical", "LowerThresholdCritical", "LowerThresholdFatal", 
        #     "MinReadingRange", "MaxReadingRange", "PhysicalContext"  ]
        #    self.voltagesNonVolatileProperties=[]
        voltagesVolatileProperties=["ReadingVolts" ]
        voltagesStatusSubProperties=["State", "Health"]

        # Add voltage sensors
        # if voltageSensors in this chassis, add them
        if chassisid in self.voltageSensorsDb:
            # set the base static properties that were assigned when the resource was created
            voltagesArray=list()
            if "Id" not in self.voltageSensorsDb[chassisid]:
                self.voltageSensorsDb[chassisid]={ "Id": {} }
            for sensorId in self.voltageSensorsDb[chassisid]["Id"]:   # sensors "0", "1", ...
                sensorData={}

                # add the required Id and MemberId properties
                sensorData["@odata.id"] = basePath + chassisid + "/Power#/Voltages/" + sensorId
                sensorData["MemberId"]  = sensorId

                # add the static properties
                for prop in self.voltagesStaticProperties:
                    if prop in self.voltageSensorsDb[chassisid]["Id"][sensorId]:
                        sensorData[prop] = self.voltageSensorsDb[chassisid]["Id"][sensorId][prop]

                # add the non-volatile properties -- xg currently empty for G5
                for prop in self.voltagesNonVolatileProperties:
                    if prop in self.voltageSensorsDb[chassisid]["Id"][sensorId]:
                        sensorData[prop] = self.voltageSensorsDb[chassisid]["Id"][sensorId][prop]

                # add the volatile properties that were assigned when the resource was created
                volatileProps = self.getVolatileProperties(voltagesVolatileProperties, "Id", sensorId,
                                self.voltageSensorsDb[chassisid], self.voltageSensorsVolatileDict[chassisid])
                for prop in volatileProps:
                    sensorData[prop] = volatileProps[prop]

                # add the status properties 
                statusProps = self.getStatusProperties(voltagesStatusSubProperties, "Id", sensorId,
                                      self.voltageSensorsDb[chassisid],
                                      self.voltageSensorsVolatileDict[chassisid])
                for prop in statusProps:
                    sensorData[prop] = statusProps[prop]

                # Add Voltage Sensor related-items 
                # if the chassis is above sled level, no related item
                if "AddRelatedItems" in self.voltageSensorsDb[chassisid]["Id"][sensorId]:
                    relatedItemMembers=list()
                    if "Chassis" in self.voltageSensorsDb[chassisid]["Id"][sensorId]["AddRelatedItems"]:
                        relatedItemMember = {"@odata.id": basePath + chassisid }
                        relatedItemMembers.append(relatedItemMember)
                    if "G5Blocks" in self.voltageSensorsDb[chassisid]["Id"][sensorId]["AddRelatedItems"]:
                        for chas in self.chassisDb:
                            if self.rfr.backend.oemUtils.isBlock(chas) is True:
                                relatedItemMember = {"@odata.id": basePath + chas}
                                relatedItemMembers.append(relatedItemMember)
                    if "G5PowerBays" in self.voltageSensorsDb[chassisid]["Id"][sensorId]["AddRelatedItems"]:
                        for chas in self.chassisDb:
                            if self.rfr.backend.oemUtils.isPowerBay(chas) is True:
                                relatedItemMember = {"@odata.id": basePath + chas}
                                relatedItemMembers.append(relatedItemMember)
                        
                    # add the RelatedItem Property to the response
                    if( len(relatedItemMembers) > 0):
                        sensorData["RelatedItem"] = relatedItemMembers

                # add the Voltages entry array to the voltage array
                voltagesArray.append(sensorData)

            # Add the new member to the Voltages array
            if "Voltages" not in responseData2:
                responseData2["Voltages"]={}
            responseData2["Voltages"] = voltagesArray



        # Add the PowerControl array
        #  Note: This initial service implementation only supports what G5 currently uses.
        #        The only properties supported are: static Name, and volatile PowerConsumedWatts
        #        Status is statically assigned Enabled, OK
        #   related structures:
        #      self.powerControlDb    from file: .../chassisDb/ PowerControlDb.json
        #      self.powerControlVolatileDict

        # set PowerControl array variables to build response from
        #  initialize these in init method
        #   self.powerControlStaticProperties=["Name","PhysicalContext" ]
        #   self.powerControlVolatileProperties=[ "PowerConsumedWatts" ]
        #   self.powerControlPowerLimitNonVolatileProperties=["LimitInWatts", "LimitException", "CorrectionInMs" ]
        powerControlStatusSubProperties=["State", "Health"]

        # add the powerControl members to the array
        if chassisid in self.powerControlDb:
            powerControlArray=list()
            if "Id" not in self.powerControlDb[chassisid]:
                self.powerControlDb[chassisid]={ "Id": {} }
            for powerControlId  in self.powerControlDb[chassisid]["Id"]:
                sensorData={}

                # add the required Id and MemberId properties
                sensorData["@odata.id"] = basePath + chassisid + "/Power#/PowerControl/" + powerControlId
                sensorData["MemberId"]  = powerControlId
 
                # add the standard static Properties that this service uses
                for prop in self.powerControlStaticProperties:
                    if prop in self.powerControlDb[chassisid]["Id"][powerControlId]:
                        sensorData[prop] = self.powerControlDb[chassisid]["Id"][powerControlId][prop]

                # add the base powerControl NonVolatile Properties that this service uses
                for prop in self.powerControlNonVolatileProperties:
                    if prop in self.powerControlDb[chassisid]["Id"][powerControlId]:
                        sensorData[prop] = self.powerControlDb[chassisid]["Id"][powerControlId][prop]

                # add the PowerLimit Non-volatile Properties that this service uses
                for prop in self.powerControlPowerLimitNonVolatileProperties:
                    if prop in self.powerControlDb[chassisid]["Id"][powerControlId]:
                        if "PowerLimit" not in sensorData:
                            sensorData["PowerLimit"]={}
                        sensorData["PowerLimit"][prop] = self.powerControlDb[chassisid]["Id"][powerControlId][prop]

                # add the volatile properties that were assigned when the resource was created
                volatileProps = self.getVolatileProperties(self.powerControlVolatileProperties, "Id", powerControlId,
                                self.powerControlDb[chassisid], self.powerControlVolatileDict[chassisid])
                for prop in volatileProps:
                    sensorData[prop] = volatileProps[prop]

                # add status to the redundancy array
                # add the status properties 
                statusProps = self.getStatusProperties(powerControlStatusSubProperties, "Id", powerControlId, 
                              self.powerControlDb[chassisid], self.powerControlVolatileDict[chassisid])
                for prop in statusProps:
                    sensorData[prop] = statusProps[prop]

                # add the related items properties
                if "AddRelatedItems" in self.powerControlDb[chassisid]["Id"][powerControlId]:
                    relatedItemMembers=list()
                    if "Chassis" in self.powerControlDb[chassisid]["Id"][powerControlId]["AddRelatedItems"]:
                        relatedItemMember = {"@odata.id": basePath + chassisid }
                        relatedItemMembers.append(relatedItemMember)
                    if "System" in self.powerControlDb[chassisid]["Id"][powerControlId]["AddRelatedItems"]:
                        if "ComputerSystems" in self.chassisDb[chassisid]:
                            sysid=self.chassisDb[chassisid]["ComputerSystems"]
                            if( len(sysid) > 0 ):
                                relatedItemMember = {"@odata.id": systemsBasePath + sysid[0] }
                                relatedItemMembers.append(relatedItemMember)
                    # add the RelatedItem Property to the response
                    if( len(relatedItemMembers) > 0):
                        sensorData["RelatedItem"] = relatedItemMembers

                powerControlArray.append(sensorData)

            # Add the new member to the Redundancy array
            if "PowerControl" not in responseData2:
                responseData2["PowerControl"]={}
            responseData2["PowerControl"] = powerControlArray



        # Add PowerSupplies array
        #
        # first: setup PowerSupply array variables to build response from
        #  self.* properties initialized in init method
        #   self.psusStaticProperties=["Name", "PowerSupplyType", "LineInputVoltageType", 
        #        "PowerCapacityWatts", "Manufacturer", "Model","SerialNumber","FirmwareVersion", 
        #        "PartNumber","SparePartNumber"  ]
        #   self.psusNonVolatileProperties=[]
        #xg-Note: Service does not support the powerSupply InputRanges array 
        #xg   add InputRange complexType to the db and add separate pseInputRangeStaticProperties 
        psusVolatileProperties=["LineInputVoltage", "LastPowerOutputWatts", "IndicatorLED" ]
        psusStatusSubProperties=["State", "Health"]

        # Create a resundancy set list to collect all of the PowerSupply redundancy group members 
        redundancySetMembers=list()

        # add PowerSupply Array properties
        if chassisid in self.powerSuppliesDb:
            psusArray=list()
            if "Id" not in self.powerSuppliesDb[chassisid]:
                self.powerSuppliesDb[chassisid]={ "Id": {} }

            # set the base static properties that were assigned when the resource was created
            for psuId in self.powerSuppliesDb[chassisid]["Id"]:   # powerSupply "0", "1", ...
                sensorData={}

                # add the required Id and MemberId properties
                sensorData["@odata.id"] = basePath + chassisid + "/Power#/PowerSupplies/" + psuId
                sensorData["MemberId"]  = psuId

                # add the static properties
                for prop in self.psusStaticProperties:
                    if prop in self.powerSuppliesDb[chassisid]["Id"][psuId]:
                        sensorData[prop] = self.powerSuppliesDb[chassisid]["Id"][psuId][prop]

                # add the non-volatile properties -- initiall empty for G5
                for prop in self.psusNonVolatileProperties:
                    if prop in self.powerSuppliesDb[chassisid]["Id"][psuId]:
                        sensorData[prop] = self.powerSuppliesDb[chassisid]["Id"][psuId][prop]

                # add the volatile properties that were assigned when the resource was created
                volatileProps = self.getVolatileProperties(psusVolatileProperties, "Id", psuId,
                                      self.powerSuppliesDb[chassisid],
                                      self.powerSuppliesVolatileDict[chassisid])
                for prop in volatileProps:
                    sensorData[prop] = volatileProps[prop]

                # add the status properties 
                statusProps = self.getStatusProperties(psusStatusSubProperties, "Id", psuId,
                                      self.powerSuppliesDb[chassisid],
                                      self.powerSuppliesVolatileDict[chassisid])
                for prop in statusProps:
                    sensorData[prop] = statusProps[prop]

                # Add PowerSupply Redundancy information
                #  if the PowerSupply entry in the PowerSupply database has a "RedundancyGroup" property,
                #  then the service will create one Redundancy member for the PowerSupply
                #  This member will point to a single redundancy group 
                if "RedundancyGroup" in self.powerSuppliesDb[chassisid]["Id"][psuId]:
                    redundancyGroup = self.powerSuppliesDb[chassisid]["Id"][psuId]["RedundancyGroup"]
                    # create the redundancy group member 
                    redundancyMember    = {"@odata.id": basePath + chassisid + "/Power#/Redundancy/" + redundancyGroup }
                    redundancySetMember = {"@odata.id": basePath + chassisid + "/Power#/PowerSupplies/" + psuId }

                    # add the member to the Redundancy array for this powerSupply 
                    # note that the service only supports one redundancy group per powerSupply
                    redundancyMembers=list()
                    redundancyMembers.append(redundancyMember)
                        
                    # add redundancyMembers to the powerSupply data
                    sensorData["Redundancy"] = redundancyMembers

                    # Finally, add the redundancy group to the redundancySet array 
                    redundancySetMembers.append(redundancySetMember)

                psusArray.append(sensorData)

            # Add the new member to the PowerSupplies (psus) array
            if "PowerSupplies" not in responseData2:
                responseData2["PowerSupplies"]={}
            responseData2["PowerSupplies"] = psusArray

        # Add the redundancy group information
        #  remember we had earlier in the function created a redundancySetMembers=list()
        #  if this has any redundancy groups in it, we create the redundancy property
        if chassisid in self.powerSuppliesDb:
            #if we collected any redundancy groups when building the PowerSupplies array, 
            # and we have a redundancy entry in the PowerSupplies db entry for the chassis, then create the redundancy entry
            if( (len(redundancySetMembers) > 0) and ("RedundancyGroup" in self.powerSuppliesDb[chassisid]) ):
                # define the list of redundancy properties
                redundancyProperties=["Name", "Mode", "MinNumNeeded", "MaxNumSupported"]
                psusRedundancyStatusSubProperties=["State", "Health"]

                redundancyArray=list()
                # set the base static properties for this redundancy group
                for redundancyGroup in self.powerSuppliesDb[chassisid]["RedundancyGroup"]:
                    sensorData={}

                    # add the required Id and MemberId properties
                    sensorData["@odata.id"] = basePath + chassisid + "/Power#/Redundancy/" + redundancyGroup
                    sensorData["MemberId"]  = redundancyGroup
 
                    # add the standard redundancyProperty Properties that this service uses
                    for prop in redundancyProperties:
                        if prop in self.powerSuppliesDb[chassisid]["RedundancyGroup"][redundancyGroup]:
                            sensorData[prop] = self.powerSuppliesDb[chassisid]["RedundancyGroup"][redundancyGroup][prop]

                    # add the RedundancySet property
                    # note that when we created the fan entries, we built the redundancySetMembers array
                    # so all we have to do is add it to the property
                    sensorData["RedundancySet"] = redundancySetMembers

                    # add status to the redundancy array
                    # add the status properties 
                    statusProps = self.getStatusProperties(psusRedundancyStatusSubProperties, "RedundancyGroup", 
                                  redundancyGroup, self.powerSuppliesDb[chassisid], self.fansVolatileDict[chassisid])
                    for prop in statusProps:
                        sensorData[prop] = statusProps[prop]

                redundancyArray.append(sensorData)

                # Add the new member to the Redundancy array
                if "Redundancy" not in responseData2:
                    responseData2["Redundancy"]={}
                responseData2["Redundancy"] = redundancyArray

        # completed creating response Data in responseData2 dict

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)


    # POST Chassis Reset  -- Reset the chassis
    def resetChassis(self, request, chassisid, resetData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
            return(4, 404, "Not Found","",hdrs)

        # verify all the required properties were sent in the request
        #  if there is no ActionsesetAllowableValues in chassisDb, then the chassis doesn't support reset
        if "ActionsResetAllowableValues" not in self.chassisDb[chassisid]:
            return(4, 404, "Not Found-Reset Not Supported for this chassis","",hdrs)

        # verify the chassis supports the resetT specified
        if "ResetType" not in resetData:
            return(4, 400, "Bad Request--Request Data does not include ResetType","",hdrs)

        if resetData["ResetType"] not in self.chassisDb[chassisid]["ActionsResetAllowableValues"]:
            return(4, 400, "Bad Request--This ResetType not supported for this chassis","",hdrs)

        resetType=resetData["ResetType"]

        # send request to reseat chassis to backend
        self.rfr.logMsg("DEBUG","--------ChassisFrontEnd: called backend.doChassisReset()")
        rc=self.rfr.backend.chassis.doChassisReset(chassisid,resetType)
        if( rc==0):
            return(0, 204, "SUCCESS", "", hdrs)
        elif( rc == 400):
            return(4,400,"invalid resetType","", hdrs)
        else:
            return(rc,500, "ERROR executing doChassisReset in backend. rc={}".format(rc), "", hdrs)

        # DONE

    # POST Chassis Reseat  -- Reseat the chassis
    def oemReseatChassis(self, request, chassisid ):
        # generate headers
        errhdrs = self.hdrs.rfRespHeaders(request)

        # verify that the chassisid is valid
        if chassisid not in self.chassisDb:
            return(4, 404, "Not Found", "", errhdrs)

        #  if there is no ActionsOemSledReseat property in chassisDb, then the chassis doesn't support reseat
        if "ActionsOemSledReseat" not in self.chassisDb[chassisid]:
            return(4, 404, "Not Found-Oem Reseat Not Supported for this chassis","", errhdrs )

        # send request to reseat chassis to backend
        self.rfr.logMsg("DEBUG","--------ChassisFrontEnd: called backend.doChassisOemReseat()")
        rc=self.rfr.backend.chassis.doChassisOemReseat(chassisid)

        if( rc==0):
            return(0, 204, "SUCCESS", "", errhdrs)
        else:
            return(rc, 500, "ERROR executing doChassisOemReseat in backend. rc={}".format(rc), "", errhdrs)

        # DONE


    def updateResourceDbsFromBackend(self, chassisid):
        if( (not "GotStaticDiscoveryInfo" in self.chassisVolatileDict[chassisid]) or
        (self.chassisVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
            self.rfr.logMsg("DEBUG","--------ChassisFrontEnd: calling backend.chassis.updateREsourceDbs()")
            updateStaticProps=True;
        else:
            # just update statics one time
            updateStaticProps=False;

        rc,resp=self.rfr.backend.chassis.updateResourceDbs(chassisid, updateStaticProps=updateStaticProps)
        if( rc==0):
            # set flag we have discovered staticDiscovery data
            self.chassisVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
        else:
            self.rfr.logMsg("ERROR","chassis.updateResourceDbsFromBackend(): Error from Backend Updating ResourceDBs: rc={}".format(rc))
        return(rc)


    # **method used to call Backend to update the "Thermal" resourceDb and resourceVolatileDict
    #   this includes:  self.tempSensorsDb[chassisid], self.tempSensorsVolatileDict[chassisid]
    #                   self.fansDb[chassisid],        self.fansVolatileDict[chassisid]
    def updateThermalResourceDbsFromBackend(self, chassisid):
        if chassisid in self.tempSensorsVolatileDict and chassisid in self.tempSensorsDb:
            # First, update tempSensors DBs
            if( (not "GotStaticDiscoveryInfo" in self.tempSensorsVolatileDict[chassisid]) or
            (self.tempSensorsVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
                self.rfr.logMsg("DEBUG","--------ChassisThermalFrontEnd: calling backend.chassis.updateTemperaturesResourceDbs()")
                updateStaticProps=True;
            else:
                # just update statics one time
                updateStaticProps=False;

            rc,resp=self.rfr.backend.chassis.updateTemperaturesResourceDbs(chassisid, updateStaticProps=updateStaticProps)
            if( rc==0):
                # set flag we have discovered staticDiscovery data
                self.tempSensorsVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
            else:
                self.rfr.logMsg("ERROR",
                     "chassis.updateTemperaturesResourceDbsFromBackend(): Error from Backend Updating TempSensors ResourceDBs: rc={}".format(rc))
                return(rc)

        # Second, update Fans DBs
        if chassisid in self.fansVolatileDict and chassisid in self.fansDb:
            if( (not "GotStaticDiscoveryInfo" in self.fansVolatileDict[chassisid]) or
            (self.fansVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
                self.rfr.logMsg("DEBUG","--------ChassisThermalFrontEnd: calling backend.chassis.updateFansResourceDbs()")
                updateStaticProps=True;
            else:
                # just update statics one time
                updateStaticProps=False;

            rc,resp=self.rfr.backend.chassis.updateFansResourceDbs(chassisid, updateStaticProps=updateStaticProps)
            if( rc==0):
                # set flag we have discovered staticDiscovery data
                self.fansVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
            else:
                self.rfr.logMsg("ERROR",
                   "chassis.updateFansResourceDbsFromBackend(): Error from Backend Updating ResourceDBs: rc={}".format(rc))
        return(rc)

    # **method used to call Backend to update the "Power" resourceDb and resourceVolatileDict
    #   this includes:  self.voltageSensorsDb[chassisid], self.voltageSensorsVolatileDict[chassisid])
    #                   self.powerControlDb[chassisid],   self.powerControlVolatileDict[chassisid])
    #                   self.powerSuppliesDb[chassisid],  self.powerSuppliesVolatileDict[chassisid])
    def updatePowerResourceDbsFromBackend(self, chassisid):
        # First, update voltage sensor DBs
        #   DBs:  self.voltageSensorsDb[chassisid], self.voltageSensorsVolatileDict[chassisid])
        
        if chassisid in self.voltageSensorsVolatileDict and chassisid in self.voltageSensorsDb:
            if( (not "GotStaticDiscoveryInfo" in self.voltageSensorsVolatileDict[chassisid]) or
            (self.voltageSensorsVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
                self.rfr.logMsg("DEBUG","--------ChassisPowerFrontEnd: calling backend.chassis.updateVoltagesResourceDbs()")
                updateStaticProps=True;
            else:
                # just update statics one time
                updateStaticProps=False;


            rc,resp=self.rfr.backend.chassis.updateVoltagesResourceDbs(chassisid, updateStaticProps=updateStaticProps)
            if( rc==0):
                # set flag we have discovered staticDiscovery data
                self.voltageSensorsVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
            else:
                self.rfr.logMsg("ERROR","chassis.updateVoltagesResourceDbsFromBackend(): Error from Backend Updating Voltages ResourceDBs: rc={}".format(rc))
                return(rc)

        if chassisid in self.powerControlVolatileDict and chassisid in self.powerControlDb:
            # Second, update PowerControl DBs
            #    DBs:   self.powerControlDb[chassisid],   self.powerControlVolatileDict[chassisid])
            if( (not "GotStaticDiscoveryInfo" in self.powerControlVolatileDict[chassisid]) or
            (self.powerControlVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
                self.rfr.logMsg("DEBUG","--------ChassisPowerFrontEnd: calling backend.chassis.updatePowerControlResourceDbs()")
                updateStaticProps=True;
            else:
                # just update statics one time
                updateStaticProps=False;

            rc,resp=self.rfr.backend.chassis.updatePowerControlResourceDbs(chassisid, updateStaticProps=updateStaticProps)
            if( rc==0):
                # set flag we have discovered staticDiscovery data
                self.powerControlVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
            else:
                self.rfr.logMsg("ERROR","chassis.updatePowerControlResourceDbsFromBackend(): Error from Backend Updating PowerControl ResourceDBs: rc={}".format(rc))
                return(rc)

        if chassisid in self.powerSuppliesVolatileDict and chassisid in self.powerSuppliesDb:
            # Third, update PowerSupplies DBs
            #    DBs:   self.powerSuppliesDb[chassisid],  self.powerSuppliesVolatileDict[chassisid])
            if( (not "GotStaticDiscoveryInfo" in self.powerSuppliesVolatileDict[chassisid]) or
            (self.powerSuppliesVolatileDict[chassisid]["GotStaticDiscoveryInfo"] is False )):
                self.rfr.logMsg("DEBUG","--------ChassisPowerFrontEnd: calling backend.chassis.updatePowerSuppliesResourceDbs()")
                updateStaticProps=True;
            else:
                # just update statics one time
                updateStaticProps=False;

            rc,resp=self.rfr.backend.chassis.updatePowerSuppliesResourceDbs(chassisid, updateStaticProps=updateStaticProps)
            if( rc==0):
                # set flag we have discovered staticDiscovery data
                self.powerSuppliesVolatileDict[chassisid]["GotStaticDiscoveryInfo"]=True
            else:
                self.rfr.logMsg("ERROR","chassis.updatePowerSuppliesResourceDbsFromBackend(): Error from Backend Updating PowerSupplies ResourceDBs: rc={}".format(rc))
            return(rc)

        return (0)


    # PATCH PowerControl:   (LimitInWatts, LimitException,CorrectionInMs)
    def patchChassisPower(self, request, chassisid, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        #first verify client didn't send us a property we cant patch
        #  the only properties that are supported for patching in RedDrum currently are:
        #       powerLimit/ limit, exception, and correction
        #     {"PowerControl": { "PowerLimit": { "LimitInWatts": <limit>, "LimitException": <exception>, "CorrectionInMs": <corr> }}}
        redfishPatchablePowerLimitProps=["LimitInWatts", "LimitException","CorrectionInMs"]

        # verify that the chassisid is valid and has a PowerControl Resource
        if chassisid not in self.powerControlDb:
            return(4,404, "Not Found", "", hdrs)

        # verify if this chassis has a patchable powercontrol
        #rts method not allowed if the Power Res is not patchable at all
        powerControlIsPatchable=False
        if "Id" in self.powerControlDb[chassisid]:
            for powerControlId  in self.powerControlDb[chassisid]["Id"]:
                if "Patchable" in self.powerControlDb[chassisid]["Id"][powerControlId]:
                    for prop in self.powerControlPowerLimitNonVolatileProperties:
                        if prop in self.powerControlDb[chassisid]["Id"][powerControlId]["Patchable"]:
                            powerControlIsPatchable=True
        if powerControlIsPatchable is False:
            return(4,405, "Method Not Allowed--PowerControl is not Writable for this Power Resource","", hdrs)

        # verify that the patch data received from the client is valid
        for prop1 in patchData:
            if( prop1 != "PowerControl" ):
                return (4,400,"Bad Request-Invalid Patch Property Sent: Not PowerControl", "", hdrs)
            else: # PowerControl:
                if len(patchData["PowerControl"]) != 1:  # xg currently only support patching PowerControl[0]
                    return (4,400,"Bad Request-PowerControl array is empty", "", hdrs)
                for prop2 in patchData["PowerControl"][0]:  # xg currently only support patching PowerControl[0]
                    if( prop2 != "PowerLimit" ):
                        return (4,400,"Invalid Patch Property Sent: Not PowerLimit", "", hdrs)
                    else:  #PowerLimit
                        for prop3 in patchData["PowerControl"][0]["PowerLimit"]:
                            if prop3 not in redfishPatchablePowerLimitProps:
                                return (4,400,"Invalid Patch Property Sent", "", hdrs)
                        for prop3 in patchData["PowerControl"][0]["PowerLimit"]:
                            if prop3 not in self.powerControlDb[chassisid]["Id"]["0"]["Patchable"]:
                                return (4,400,"Property not patachable in this chassis", "", hdrs)

        #now update the databases and patch the valid properties sent
        patchPowerLimitDict =patchData["PowerControl"][0]["PowerLimit"] # xg currently only support patching PowerControl[0]
        for prop in redfishPatchablePowerLimitProps:
            if( prop in patchPowerLimitDict):
                propVal=patchPowerLimitDict[prop]
                # update the powerControl database - xg currently we only support patching powerControl[0]
                self.powerControlDb[chassisid]["Id"]["0"][prop]=propVal
                backendPatchDict=dict()
                backendPatchDict[prop]=propVal
                rc=self.rfr.backend.chassis.patchPowerControl(chassisid, backendPatchDict)
                if rc != 0:
                    return(rc,500, "ERROR from backend esecuting patchPowerControl. rc={}".format(rc), "", hdrs)

        return(0,204, "", "", hdrs)
        

