
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import copy
import sys
import datetime
import pytz
from  .redfish_headers import RfAddHeaders

class RfManagersResource():       
    # Class for all resources under /redfish/v1/Managers
    # Note that this resource was created in serviceRoot for the Managers Resource.
    def __init__(self,rfr ):
        self.rfr=rfr
        self.rdr=rfr
        self.managersDbDiscovered=None
        self.loadResourceTemplates(rfr )
        self.loadManagersDbFiles(rfr)
        self.hdrs=RfAddHeaders(rfr)

        self.staticProperties=["Name", "Description", "ManagerType", "ServiceEntryPointUUID", "UUID", "Model" ]
        self.nonVolatileProperties=[ "FirmwareVersion" ]
        self.oemDellG5NonVolatileProps = ["LastUpdateStatus","SafeBoot","OpenLookupTableVersion"]
        self.magic="123456"

    def loadResourceTemplates( self, rfr ):
        # these are very bare-bones templates but we want to be able to update the resource version or context easily
        #   so the approach is to always start with a standard template for each resource type

        #load ManagersCollection Template
        self.managersCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates","ManagerCollection.json")

        #load ManagerEntry Template
        self.managerEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates","Manager.json")

        #load ManagerNetworkProptocol Template
        self.managerNetworkProtocolTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates","ManagerNetworkProtocol.json")

        #load Manager  EthernetInterfaceCollection Template
        self.managerEthernetInterfaceCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates","EthernetInterfaceCollection.json")

        #load Manager  EthernetInterface  Template
        self.managerEthernetInterfaceTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates","EthernetInterface.json")

        #load Manager  SerialInterfaceCollection  Template
        #xg TODO
        #load Manager  SerialInterface Template
        #xg TODO


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
            self.rfr.logMsg("CRITICAL","*****ERROR: Manager Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
            sys.exit(10)

    def loadManagersDbFiles(self,rfr ):
        # if rfr.useCachedDiscoveryDb is True:
        #   then if the managers database files exist in /var/www/rf/managersDb/* then load them to in-memory dict
        #        else if rfr.useStaticResourceDiscovery=True, read static db files and save to the cache
        #        else,  kick-off job to discover the managers data from the MC
        # else, always run full discovery each time RM Redfish Service starts
        self.managersDbDiscovered=False
        if rfr.useCachedDiscoveryDb is True:
            # first make sure all of the manager DB files exist
            managersDbCacheExists=True
            managersDbFiles=["ManagersDb.json" ]
            for filenm in managersDbFiles:
                managersDbFilePath=os.path.join(rfr.varDataPath,"managersDb", filenm)
                if not os.path.isfile(managersDbFilePath):
                    managersDbCacheExists = False
                    break
            # then load them into dictionaries
            if managersDbCacheExists is True:
                self.managersDb=self.loadManagerDbFile(rfr.varDataPath, "managersDb", "ManagersDb.json") 
                self.managersDbDiscovered=True

        return(0)

    # worker function to load CACHED manager db file into dict
    def loadManagerDbFile( self, dataPath, subDir, filename ):
        filePath=os.path.join(dataPath, subDir, filename)
        if os.path.isfile(filePath):
            response=json.loads( open(filePath,"r").read() )
            return(response)
        else:
            self.rfr.logMsg("CRITICAL","*****ERROR: Manager Resource: Json Data file:{} Does not exist. Exiting.".format(filePath))
            sys.exit(10)


    # clear the current manager Db Dicts and HDD caches
    def clearManagersResourceCaches(self,rfr):
        self.managersDb=self.clearManagersDbFile(rfr, "managersDb", "ManagersDb.json") 
        self.managersDbDiscovered=False

    # worker function for above clear managers resource caches 
    def clearManagersDbFile( self, rfr, subDir, filename ):
        clearedDb=dict()
        varDbFilePath=os.path.join(rfr.varDataPath, subDir, filename)
        #jsonEmptyDb=json.dumps(clearedDb,indent=4)
        #with open( varDbFilePath, 'w', encoding='utf-8') as f:
        #        f.write(jsonEmptyDb)
        if os.path.exists(varDbFilePath):
            os.remove(varDbFilePath)
        return(clearedDb)


    # worker function to write the manager Db Dict back to the STATIC manager db file
    # used by patch
    def updateStaticManagersDbFile( self ):
        varDbFilePath=os.path.join(self.rfr.varDataPath, "managersDb", "ManagersDb.json")
        responseJson=json.dumps(self.managersDb, indent=4)
        with open( varDbFilePath, 'w', encoding='utf-8') as f:
            f.write(responseJson)
        return(0)


    def initializeManagersVolatileDict(self,rfr):
        # this is the in-memory dict of volatile Managers properties
        self.managersVolatileDict=dict()   #create an empty dict of Managers entries

        # initialize the Volatile Dicts
        for managerid in self.managersDb:
            # inialize with empty members for all known manager
            self.managersVolatileDict[managerid]={}


    # GET Managers Collection
    def getManagersCollectionResource(self, request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.managersCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # first copy the Managers Collection template 
        # then updates the Members array will each manager previously discovered--in ManagersDb 

        # copy the ManagersCollection template file (which has an empty roles array)
        responseData2=dict(self.managersCollectionTemplate)
        count=0
        # now walk through the entries in the managersDb and build the managersCollection Members array
        # note that the members array is an empty array in the template
        uriBase="/redfish/v1/Managers/"
        for managerid in self.managersDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=uriBase + managerid
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)



    # GET Manager Entry
    def getManagerEntry(self, request, managerid):
        # generate error header for 4xx errors
        errhdrs=self.hdrs.rfRespHeaders(request)

        # verify that the managerid is valid
        if managerid not in self.managersDb:
                return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="GetPatch",
                                     resource=self.managerEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.managerEntryTemplate)

        # setup some variables to build response from
        basePath="/redfish/v1/Managers/"

        #self.staticProperties=["Name", "Description", "ManagerType", "ServiceEntryPointUUID", "UUID", "Model" ]
        #self.nonVolatileProperties=[ "FirmwareVersion" ]
        #self.oemDellG5NonVolatileProps = ["LastUpdateStatus","SafeBoot","OpenLookupTableVersion"]
        volatileProperties=[ "IndicatorLED", "PowerState","DateTime","DateTimeLocalOffset"]
        baseNavProperties=["LogServices", "EthernetInterfaces", "SerialInterfaces","NetworkProtocol","VirtualMedia"]
        statusSubProperties=["State", "Health"]
        linkNavProperties=["ManagerForServers", "ManagerForChassis", "ManagerInChassis" ]
        serialConsoleSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]
        graphicalConsoleSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]
        commandShellSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]

        # assign the required properties
        responseData2["@odata.id"] = basePath + managerid
        responseData2["Id"] = managerid


        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        rc=self.updateResourceDbsFromBackend(managerid)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getManagerEntry(): updateResourceDbsFromBackend() returned error ")
            return(9, 500, "Internal Error", "", errhdrs)

        # set the base static properties that were assigned when the resource was created
        for prop in self.staticProperties:
            if prop in self.managersDb[managerid]:
                responseData2[prop] = self.managersDb[managerid][prop]

        # get the base non-volatile properties that were assigned when the resource was created
        # these are stored in the persistent cache but are not static--ex is assetTag
        for prop in self.nonVolatileProperties:
            if prop in self.managersDb[managerid]:
                responseData2[prop] = self.managersDb[managerid][prop]

        # get the serialConsole  properties 
        if "SerialConsole" in self.managersDb[managerid]:
            for subProp in serialConsoleSubProperties:
                if subProp in self.managersDb[managerid]["SerialConsole"]:
                    if "SerialConsole" not in responseData2:
                        responseData2["SerialConsole"]={}
                    responseData2["SerialConsole"][subProp] = self.managersDb[managerid]["SerialConsole"][subProp]

        #xg11C serialConsoleSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]
        #xg11C graphicalConsoleSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]
        #xg11C commandShellSubProperties=["ServiceEnabled","MaxConcurrentSessions","ConnectTypesSupported"]

        # get the graphicalConsole  properties 
        if "GraphicalConsole" in self.managersDb[managerid]:
            for subProp in graphicalConsoleSubProperties:
                if subProp in self.managersDb[managerid]["GraphicalConsole"]:
                    if "GraphicalConsole" not in responseData2:
                        responseData2["GraphicalConsole"]={}
                    responseData2["GraphicalConsole"][subProp] = self.managersDb[managerid]["GraphicalConsole"][subProp]

        # get the commandShel  properties 
        if "CommandShell" in self.managersDb[managerid]:
            for subProp in commandShellSubProperties:
                if subProp in self.managersDb[managerid]["CommandShell"]:
                    if "CommandShell" not in responseData2:
                        responseData2["CommandShell"]={}
                    responseData2["CommandShell"][subProp] = self.managersDb[managerid]["CommandShell"][subProp]


        # get the volatile properties eg powerState
        volatileProps = self.getVolatileProperties(volatileProperties, None, None,
                        self.managersDb[managerid], self.managersVolatileDict[managerid])
        for prop in volatileProps:
            responseData2[prop] = volatileProps[prop]

        # check if we are constructing datetime from the Manager OS
        # this overrides anything that was retrieved from 
        #         volatileProperties=[ "IndicatorLED", "PowerState","DateTime","DateTimeLocalOffset"]
        if "GetDateTimeFromOS" in self.managersDb[managerid]:
            datetimeManagerOsUtc = datetime.datetime.now(pytz.utc).replace(microsecond=0).isoformat('T')
            datetimeOffsetManagerOsUtc="+00:00"
            responseData2["DateTime"] = datetimeManagerOsUtc
            responseData2["DateTimeLocalOffset"] = datetimeOffsetManagerOsUtc

        # check if we are constructing manager/UUID from the ServiceRoot UUID
        if "GetUuidFromServiceRoot" is True:
            responseData2["UUID"] = self.rfr.root.resData["UUID"]

        # check if we are constructing manager/ServiceEntryPointUUID from the UUID in ServiceRoot
        #    this overrides anything that was retrieved from self.staticProperties=["Name", ... "ServiceEntryPointUUID", "UUID", "Model" ]
        if "GetServiceEntryPointUuidFrom" in self.managersDb[managerid]:
            if self.managersDb[managerid]["GetServiceEntryPointUuidFrom"] == "ServiceRoot":
                responseData2["ServiceEntryPointUUID"] = self.rfr.root.resData["UUID"]


        # get the status properties
        statusProps = self.getStatusProperties(statusSubProperties, None, None,
                      self.managersDb[managerid], self.managersVolatileDict[managerid])
        for prop in statusProps:
            responseData2[prop] = statusProps[prop]


        # baseNavProperties=["LogServices", "EthernetInterfaces", "SerialInterfaces","NetworkProtocol","VirtualMedia"]
        # set the base navigation properties:   /redfish/v1/Managers/<baseNavProp>
        for prop in baseNavProperties:
            if "BaseNavigationProperties" in self.managersDb[managerid]:
                if prop in self.managersDb[managerid]["BaseNavigationProperties"]:
                    responseData2[prop] = { "@odata.id": basePath + managerid + "/" + prop }

        # build the Actions data
        if "ActionsResetAllowableValues" in self.managersDb[managerid]:
            resetAction = { "target": basePath + managerid + "/Actions/Manager.Reset",
                "ResetType@Redfish.AllowableValues": self.managersDb[managerid]["ActionsResetAllowableValues"] }
            if "Actions" not in responseData2:
                responseData2["Actions"]={}
            responseData2["Actions"]["#Manager.Reset"]= resetAction

        # Build the Oem Actions
        if "AddOemActions" in self.managersDb[managerid] and "Actions" in self.managersDb[managerid]:
            oemActions=dict()
            if "Oem" in self.managersDb[managerid]["Actions"]:
                for oemaction in self.managersDb[managerid]["Actions"]["Oem"]:
                    #make a copy as we will remove some properties
                    thisAction=copy.deepcopy(self.managersDb[managerid]["Actions"]["Oem"][oemaction])
                    if "target" in thisAction and "targetId" in thisAction:
                        thisAction["target"] = basePath + managerid + "/Actions/Oem/" + thisAction["targetId"]
                        del thisAction["targetPath"]
                        del thisAction["targetId"]
                    oemActions[oemaction]=thisAction
 
            if "Actions" not in responseData2:
                responseData2["Actions"]={}
                if "Oem" not in responseData2["Actions"]:
                    responseData2["Actions"]["Oem"]={}
            responseData2["Actions"]["Oem"] = oemActions

        # build Dell OEM Section 
        if "OemDellG5MCMgrInfo" in self.managersDb[managerid]:
            # define the legal oem properties 
            # moved to __init__():  self.oemDellG5NonVolatileProps = ["LastUpdateStatus","SafeBoot","OpenLookupTableVersion"]

            # check if  each of the legal oem subProps are in the db
            oemData={}
            for prop in self.oemDellG5NonVolatileProps:
                if prop in self.managersDb[managerid]["OemDellG5MCMgrInfo"]:
                    # since these sub-properties are nonVolatile, read them from the database
                    oemData[prop]=self.managersDb[managerid]["OemDellG5MCMgrInfo"][prop]

            if "Oem" not in responseData2:
                responseData2["Oem"]={}
            responseData2["Oem"]["Dell_G5MC"] = oemData

        # build the navigation properties under Links : "ManagerForChassis", "ManagerInChassis", ManagerForServers
        responseData2["Links"]={}
        for navProp in linkNavProperties:
            if navProp in self.managersDb[managerid]:
                #first do single entry nav properties
                if( navProp == "ManagerInChassis" ):
                    linkBasePath="/redfish/v1/Chassis/"
                    member= { "@odata.id": linkBasePath + self.managersDb[managerid][navProp] }
                    responseData2["Links"][navProp] = member
                #otherwise, handle an array or list of nav properties
                else: 
                    if( navProp == "ManagerForChassis" ):
                        linkBasePath="/redfish/v1/Chassis/"
                    elif( navProp == "ManagerForServers") :
                        linkBasePath="/redfish/v1/Systems/"
                    else: # unknown assume managers here
                        linkBasePath="/redfish/v1/Managers/"

                    #start with an empty array
                    members = list()
                    # now create the array of members for this navProp
                    for memberId in self.managersDb[managerid][navProp]:
                        newMember= { "@odata.id": linkBasePath + memberId }
                        members.append(newMember)
                    # now add the members array to the response data
                    responseData2["Links"][navProp] = members


        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)



    # PATCH manager
    # returns: rc,statusCode,ErrString,resp,hdr
    def patchManagerEntry(self, request, managerid, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the managerid is valid
        if managerid not in self.managersDb:
            return(4,404, "Not Found", "", hdrs)

        # define the patchable properties in Manager Resource
        patchableInRedfishProperties=["DateTime","DateTimeLocalOffset"]
        patchableInRedfishComplexTypeManagerService=["SerialConsole","CommandShell","GraphicalConsole"]
        patchableInRedfishComplexTypeManagerServiceSupProperty="ServiceEnabled" # only one property is patchable

        #first verify client didn't send us a property we cant patch based on Redfish Schemas
        for prop in patchData:
            if prop in patchableInRedfishComplexTypeManagerService:
                for subProp in prop:
                    if subProp != patchableInRedfishComplexTypeManagerServiceSubProperty:
                        return(4, 400, "Bad Request. Property: {}, subProperty {} not patachable per Redfish Spec".format(
                              prop,subProp), "", hdrs)
            elif prop not in patchableInRedfishProperties: 
                return(4, 400, "Bad Request. Property: {} not patachable per Redfish Spec".format(prop), "", hdrs)

        #second check if this instance of manager has a list of Patchable properties- if not, no patches are allowed
        #  if there is no Patchable property in managersDb, then nothing is patchable
        if "Patchable" not in self.managersDb[managerid]:
            return(4, 400, "Bad Request. Resource is not patachable", "", hdrs)

        # third, check if the specific property is patchable for this instance of manager--from discovery data
        for prop in patchData:
            if prop not in self.managersDb[managerid]["Patchable"]:
                return(4, 400, "Bad Request. Property: {} not patachable for this resource".format(prop), "", hdrs)

        # verify that the patch data has proper format
        #     patch properties:   DateTime, DateTimeLocalOffset,   

        # **make calls to Backend to update the resourceDb and resourceVolatileDict
        #   this insures that the volDb is updated with all volatile properties
        rc=self.updateResourceDbsFromBackend(managerid)
        if( rc != 0):
            self.rfr.logMsg("Error","patchManagerEntry(): updateResourceDbsFromBackend returned error ")
            return(5, 500, "Internal Error: Error getting resource Update from Backend", "", hdrs) 

        # xgFIX check if the patch property should be handled by Frontend
        dateTimeFromOs=False
        if "GetDateTimeFromOS" in self.managersDb[managerid] and self.managersDb[managerid]["GetDateTimeFromOS"] is True:
            dateTimeFromOs=True
            if "DateTime" in patchData or "DateTimeLocalOffset" in patchData:
                # handle patching these here:
                if "DateTime" in patchData:
                    #xg9999 set time
                    dateTimeIsProp=True
                    print(" ======= DEBUG: PatchManager-DateTime: {}".format(patchData["DateTime"]))
                if "DateTimeLocalOffset" in patchData:
                    #xg9999 set timeoffset
                    print(" ======= DEBUG: PatchManager-DateTimeLocalOffset: {}".format(patchData["DateTimeLocalOffset"]))
                #datetimeUtc = datetime.datetime.now(pytz.utc).replace(microsecond=0).isoformat('T')
                #datetimeOffsetUtc="+0000"
                # xgTODO xg9999 update here in frontend
                # the backend will ignore these

        # now construct the patch data, and update the volatileDict or resourceDb
        # send separate patches for each patch property, 
        updateManagersDb=False
        for prop in patchData:
            if (dateTimeFromOs is True) and (prop=="DateTime" or prop=="DateTimeLocalOffset"):
                # we have already handled this case above
                pass
            elif prop in self.managersVolatileDict[managerid]:
                    self.managersVolatileDict[managerid][prop]=patchData[prop]
                    reqPatchData={ prop: patchData[prop]}
                    rc=self.rfr.backend.managers.doPatch(managerid, reqPatchData)
            elif prop in self.managersDb[managerid]:
                    self.managersDb[managerid][prop]=patchData[prop]
                    reqPatchData={ prop: patchData[prop]}
                    rc=self.rfr.backend.managers.doPatch(managerid, reqPatchData)
                    updateManagersDb=True
            else:
                    pass

        if updateManagersDb is True:
            self.updateStaticManagersDbFile()

        # update volatile struct with patch time
        curTime=datetime.datetime.utcnow()
        self.managersVolatileDict[managerid]["UpdateTime"]=curTime

        return(0, 204, "", "", hdrs)



    # **make calls to Backend to update the resourceDb and resourceVolatileDict
    # The first--if we havent already, get staticDiscoverySystemsInfo
    def updateResourceDbsFromBackend(self, managerid):
        if( (not "GotStaticDiscoveryInfo" in self.managersVolatileDict[managerid]) or
        (self.managersVolatileDict[managerid]["GotStaticDiscoveryInfo"] is False )):
            self.rfr.logMsg("DEBUG","--------ManagersFrontEnd: calling backend.managers.updateREsourceDbs()")
            updateStaticProps=True;
        else:
            # just update statics one time
            updateStaticProps=False;

        rc,resp=self.rfr.backend.managers.updateResourceDbs(managerid, updateStaticProps=updateStaticProps)
        if( rc==0):
            # set flag we have discovered staticDiscovery data
            self.managersVolatileDict[managerid]["GotStaticDiscoveryInfo"]=True
        else:
            self.rfr.logMsg("ERROR","managers.updateResourceDbsFromBackend(): Error from Backend Updating ResourceDBs: rc={}".format(rc))
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
                    # elif the prop was assigned a default value in Db, then use that
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
                    else:
                        if "Status" not in resp:
                            resp["Status"]={}
                        resp["Status"][subProp] = resourceDb["Status"][subProp]
        return(resp)



    # POST Manager Reset  -- Reset Manager
    def resetManager(self, request, managerid, resetData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # verify that the managerid is valid
        if managerid not in self.managersDb:
            return(4, 404, "Not Found","",hdrs)

        #  if there is no ResetAllowable value property in managersDb, then the manager doesn't support reset
        if "ActionsResetAllowableValues" not in self.managersDb[managerid]:
            return(4, 404, "Not Found","",hdrs)

        # verify all the required properties were sent in the request
        if "ResetType" not in resetData:
            return(4,400,"Required  request property not included in request","",hdrs)
        else:
            # get the resetValue
            resetValue=resetData["ResetType"]

        # check if this is a valid resetType for Redfish 
        redfishValidResetValues=["On","ForceOff","GracefulShutdown","GracefulRestart","ForceRestart",
                                 "Nmi","ForceOn","PushPowerButton","PowerCycle"]
        if resetValue not in redfishValidResetValues:
            return(4,400,"invalid resetType","",hdrs)

        # check if this is a resetType that this manager does not support
        if resetValue not in self.managersDb[managerid]["ActionsResetAllowableValues"]:
            return(4,400,"invalid resetType","",hdrs)

        # if here we have a valid request and valid resetValue 
        # send request to reset manager to backend
        self.rdr.logMsg("DEBUG","--------ManagersFrontEnd: called backend.doManagerReset()ResetType: {}".format(resetValue))
        rc=self.rdr.backend.managers.doManagerReset(managerid,resetValue)


        if( rc==0):
            return(0, 204, "", "", hdrs)
        else:
            self.rdr.logMsg("DEBUG","--------ManagersFrontEnd: got err sending Reset to backend. rc: {}".format(rc))
            return(rc,500, "ERROR executing backend reset","",hdrs)

        # DONE


    # GET ManagerNetworkProtocol
    def getManagerNetworkProtocol(self, request, mgrid):
        # generate error header for 4xx errors
        errhdrs=self.hdrs.rfRespHeaders(request)

        # verify that the managerid is valid
        if mgrid not in self.managersDb:
            return(4, 404, "Not Found", "", errhdrs)

        if "BaseNavigationProperties" not in self.managersDb[mgrid]:
            return(4, 404, "Not Found", "", errhdrs)

        if "NetworkProtocol" not in self.managersDb[mgrid]["BaseNavigationProperties"]:
            return(4, 404, "Not Found", "", errhdrs)

        #if "NetworkProtocols" not in self.managersDb[mgrid]:
        #    return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.managerNetworkProtocolTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # first just copy the template resource
        responseData2=dict(self.managerNetworkProtocolTemplate)

        # setup some variables to build response from
        basePath="/redfish/v1/Managers/"
        networkProtocolProperties=["Name","HTTP","HTTPS","SSH", "NTP","HostName","FQDN","Telnet","Status"
                                   "VirtualMedia","SSDP","IPMI","KVMIP" ]

        # assign the required properties
        responseData2["@odata.id"] = basePath + mgrid + "/NetworkProtocol"
        responseData2["Id"] = mgrid + "NetworkProtocol"
        responseData2["Description"] = "Network Protocol Information for Manager" + mgrid

        # **make calls to Backend to update the resourceDb 
        rc=self.rfr.backend.managers.updateManagerNetworkProtocolsDbFromBackend(mgrid,noCache=False)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getManagerNetworkProtocols(): updateManagerNetworkProtocols backend returned error ")
            return(9, 500, "Internal Error", "", errhdrs)

        # set the base static properties that were assigned when the resource was created
        if "NetworkProtocols" in self.managersDb[mgrid]:
            for prop in networkProtocolProperties:
                if prop in self.managersDb[mgrid]["NetworkProtocols"]:
                    responseData2[prop] = self.managersDb[mgrid]["NetworkProtocols"][prop]

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)



    # GET Manager Ethernet Interfaces Collection
    def getManagerEthernetInterfaces(self, request, mgrid):
        # verify that the managerid is valid
        if mgrid not in self.managersDb:
            notFound=True
        elif "BaseNavigationProperties" not in self.managersDb[mgrid]:
            notFound=True
        elif "EthernetInterfaces" not in self.managersDb[mgrid]["BaseNavigationProperties"]:
            notFound=True
        else:
            notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4,404,"Not Found","",errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.managerEthernetInterfaceCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # **make calls to Backend to update the resourceDb 
        rc=self.rfr.backend.managers.updateManagerEthernetEnterfacesDbFromBackend(mgrid, noCache=False)
        if( rc != 0):
            self.rfr.logMsg("ERROR","getManagerEthernetInterfaces(): updateManagerEthernetInterfaces backend returned error ")
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(9, 500, "Internal Error", "", errhdrs)

        # first just copy the template resource
        responseData2=dict(self.managerEthernetInterfaceCollectionTemplate)
        odataId = "/redfish/v1/Managers/" + mgrid + "/EthernetInterfaces"
        responseData2["@odata.id"] = odataId
        uriBase = odataId + "/"
        responseData2["Description"] = "Manager EthernetInterface Collection"

        count=0
        # now walk through the entries in the Manager EthernetInterfaceDb and build the Members array
        # note that the members array is an empty array in the template
        if "EthernetInterfaces" in self.managersDb[mgrid]:
            for ethid in self.managersDb[mgrid]["EthernetInterfaces"]:
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



    # GET Manager Ethernet Interface Entry
    def getManagerEthernetInterfaceEntry(self, request, mgrid, ethid):
        # verify that the systemid and procId is valid:
        if mgrid not in self.managersDb:
            notFound=True
        elif "BaseNavigationProperties"  not in  self.managersDb[mgrid]:
            notFound=True
        elif "EthernetInterfaces" not in self.managersDb[mgrid]["BaseNavigationProperties"]:
            notFound=True
        else:
            # **make calls to Backend to update the resourceDb 
            #   the backend will query the node if the processorsDb is not up to date
            rc=self.rfr.backend.managers.updateManagerEthernetEnterfacesDbFromBackend(mgrid, noCache=False, ethid=ethid)
            if( rc != 0):
                errMsg="ERROR updating Manager Ethernet Interface info from backend. rc={}".format(rc)
                self.rfr.logMsg("ERROR",errMsg)
                errhdrs=self.hdrs.rfRespHeaders(request)
                return(9, 500, "Internal Error", "", errhdrs)

            # verify the the procid is valid
            if mgrid not in self.managersDb or "EthernetInterfaces" not in self.managersDb[mgrid]:
                notFound=True
            elif ethid not in self.managersDb[mgrid]["EthernetInterfaces"]:
                notFound=True
            else:
                thisDbEntry = self.managersDb[mgrid]["EthernetInterfaces"][ethid]
                notFound=False

        if notFound is True:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "", errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow="Get",
                                     resource=self.managerEthernetInterfaceTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        mgrEthernetProperties=["Name", "UefiDevicePath", "Status", "InterfaceEnabled", "PermanentMACAddress",
                "MACAddress", "SpeedMbps", "AutoNeg", "FullDuplex", "MTUSize", "HostName", "FQDN",
                "MaxIPv6StaticAddresses", "VLAN", "IPv4Addresses", "IPv6Addresses", "IPv6StaticAddresses",
                "IPv6AddressPolicyTable","IPv6DefaultGateway","NameServers", "VLANs"]

        mgrIpv4SubProperties=["Gateway","AddressOrigin", "SubnetMask", "Address"]

        # xg99 add IPV6 properties

        # copy the template resource and update odata.id since it is a funct of mgrid
        responseData2=dict(self.managerEthernetInterfaceTemplate)
        odataId = "/redfish/v1/Managers/" + mgrid + "/EthernetInterfaces/" + ethid
        responseData2["@odata.id"] = odataId
        responseData2["Id"] = ethid
        responseData2["Description"] = "Manager Ethernet Interface Properties"

        # get the base properties
        for prop in mgrEthernetProperties:
            if prop in thisDbEntry:
                responseData2[prop] = thisDbEntry[prop]

        # get the IPv4 sub-properties
        if "IPv4Addresses" in thisDbEntry:
            ipv4Addresses = []
            for member in thisDbEntry["IPv4Addresses"]:
                ipv4Member={}
                for prop in mgrIpv4SubProperties:
                    if prop in member:
                        ipv4Member[prop] = member[prop]
                ipv4Addresses.append(ipv4Member)
            responseData2["IPv4Addresses"] = ipv4Addresses

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, respHdrs)


    # Oem Manager Action  
    def oemManagerAction(self, request, managerid, actionid, rdata):
        # verify that the managerid is valid:
        errhdrs=self.hdrs.rfRespHeaders(request)
        if managerid not in self.managersDb:
            return(4, 404, "Not Found - managerId not found", "", errhdrs)
        elif "AddOemActions" not in  self.managersDb[managerid] and self.managersDb[managerid] is not True:
            return(4, 404, "Not Found - OEM Actions not supported by manager", "", errhdrs)
        elif "Actions" not in self.managersDb[managerid] or "Oem" not in self.managersDb[managerid]["Actions"]:
            # need to update the manager db
            rc=self.updateResourceDbsFromBackend(managerid)
            if( rc != 0):
                self.rfr.logMsg("ERROR","getManagerEntry(): updateResourceDbsFromBackend() returned error ")
                return(9, 500, "Internal Error", "", errhdrs)
            if "Actions" not in self.managersDb[managerid] or "Oem" not in self.managersDb[managerid]["Actions"]:
                return(4, 404, "Not Found - no oem actions for this manager", "", errhdrs)
        else:
            pass
            # no errors found in frontend - backend will verify that the actionid is ok

        # if here we have a valid request 
        # send request to backend
        self.rdr.logMsg("DEBUG","--------ManagersFrontEnd: called backend.doOemManagerAction. actionId: {}".format(actionid))
        rc,statusCode,errMsg, resp=self.rdr.backend.managers.doOemManagerAction(managerid, actionid, rdata)

        # generate headers xg9 not sure if special headers are returned?
        hdrs = self.hdrs.rfRespHeaders(request)

        # xg99 not sure what idrac returns, I'm returning empty string data here
        if( rc==0):
            statusCode=204
            return(0, statusCode, errMsg, "", hdrs)
        else:
            self.rdr.logMsg("DEBUG","--------ManagersFrontEnd: got err sending Reset to backend. rc: {}".format(rc))
            return(rc,500, "ERROR executing backend reset","",hdrs)

