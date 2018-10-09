
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys

from  .resource         import  RfStaticResource 
from  .sessionService   import RfSessionService
from  .accountService   import RfAccountService
from  .eventService     import RfEventService
from  .jsonSchemas      import RfJsonSchemas
from  .registries       import RfRegistries

from  .redfish_headers  import RfAddHeaders


# called from main: RfServiceRoot(rfr )

class RfServiceRoot():       
    def __init__(self, rfr):
        self.magic="123456789"
        self.varDataPathDirs(rfr)
        self.clearCachesOnReset(rfr)
        self.loadServiceRootDict(rfr)
        self.createSubObjects(rfr)
        self.finalInitProcessing(rfr)


    def varDataPathDirs(self, rfr):
        # assign the paths
        dbPath=os.path.join(rfr.varDataPath, "db")

        # check if the varDataPath directories exists and create them if not
        if not os.path.exists(rfr.varDataPath):
            os.makedirs(rfr.varDataPath)
        if not os.path.exists(dbPath):
            os.makedirs(dbPath)
        return(0)

    def loadServiceRootDict(self,rfr):
        # load service root dict from template file
        rootFilePath=os.path.join(rfr.baseDataPath,"templates", "ServiceRoot.json")
        if os.path.isfile(rootFilePath):
            self.resData=json.loads( open(rootFilePath,"r").read() )
        else:
            rfr.logMsg("CRITICAL", "*****Json Data file:{} Does not exist. Exiting.".format(rootFilePath))
            sys.exit(10)

        # check if there is a ServiceRootUuidDb.json file in var path, and load it if there is
        uuidFilePath=os.path.join(rfr.varDataPath, "db", "ServiceRootUuidDb.json")
        if os.path.isfile(uuidFilePath):
            uuidDb=json.loads( open(uuidFilePath,"r").read() )
        else:
            rfr.logMsg("WARNING", "*****Json Data file:{} Does not exist. Creating default.".format(uuidFilePath))
            # generate a random uuid 
            import uuid
            uuidString=str(uuid.uuid4())
            uuidDb={"UUID": uuidString }

            #write the data back out to the var directory where the dynamic uuid db file is kept
            uuidDbJson=json.dumps(uuidDb,indent=4)
            with open( uuidFilePath, 'w', encoding='utf-8') as f:
                f.write(uuidDbJson)

        # now write the uuid to the serviceRoot resource data
        self.resData["UUID"]=uuidDb["UUID"]


    def clearCachesOnReset(self, rfr):
        # check if any of the flags are set to clear Caches on Redfish Service Restart.
        #    If so, clear the caches here
        # ServiceRootVars.json is a json file of form: 
        #   { "ClearHwResourceCaches": false, "ClearAccountsCaches": false, "ClearUuid": false }

        # set path to ServiceRootVars.json
        serviceRootVarsPath=os.path.join(rfr.varDataPath, "db", "ServiceRootVars.json")

        # if there is a db/ServiceRootVars.json file, read it to get the vars
        # else: otherwise, assume no vars set and don't do anything
        if os.path.isfile(serviceRootVarsPath):
            resourceVars=json.loads( open(serviceRootVarsPath,"r").read() )

            updateServiceRootVars=False
            # if ClearHwResourceCaches is true, clear them
            if "ClearHwResourceCaches" in resourceVars:
                if resourceVars["ClearHwResourceCaches"] is True:
                    updateServiceRootVars=True
                    rdata={"ClearOn": "Startup" }
                    rc,err,errmsg,d=clearHwResourceCaches(self,rfr,rdata)
                    if rc != 0:
                        rfr.logMsg("ERROR","Error Clearing HW Resource Caches: rc={}".format(rc))
                    resourceVars["ClearHwResourceCaches"]=False

            # if ClearAccountsCaches   is true, clear them
            if "ClearAccountsCaches" in resourceVars:
                if resourceVars["ClearAccountsCaches"] is True:
                    updateServiceRootVars=True
                    rdata={"ClearOn": "Startup" }
                    rc,err,errmsg,d=clearAccountsCaches(self,rfr,rdata)
                    if rc != 0:
                        rfr.logMsg("ERROR","Error Clearing Accounts Caches: rc={}".format(rc))
                    resourceVars["ClearAccountsCaches"]=False

            # if ClearUuid   is true, clear it
            if "ClearUuid" in resourceVars:
                if resourceVars["ClearUuid"] is True:
                    uuidFilePath=os.path.join(rfr.varDataPath, "db", "ServiceRootUuidDb.json")
                    if os.path.isfile(uuidFilePath):
                        updateServiceRootVars=True
                        os.remove(uuidFilePath)
                        resourceVars["ClearUuid"]=False

            # if any of the vars were updated, update the ServiceRootVars.json file
            if updateServiceRootVars is True:
                jsonResourceVarsData=json.dumps(resourceVars,indent=4)
                with open(serviceRootVarsPath, 'w', encoding='utf-8') as f:
                    f.write( jsonResourceVarsData )

        return(0)

    def setServiceRootVars(self, rfr, varProperty, varValue):
        # verify it is a predefined var
        serviceRootVarsList=("ClearHwResourceCaches", "ClearAccountsCaches", "ClearUuid")
        if varProperty not in serviceRootVarsList:
            rfr.logMsg("WARNING","Setting unknown ServiceRoot VAR: rc={}.  continuing...".format(varProperty))

        # set path to ServiceRootVars.json
        serviceRootVarsPath=os.path.join(rfr.varDataPath, "db", "ServiceRootVars.json")

        # if there is a db/ServiceRootVars.json file, read it to get the vars
        # else: create empty dict
        if os.path.isfile(serviceRootVarsPath):
            resourceVars=json.loads( open(serviceRootVarsPath,"r").read() )
        else:
            resourceVars=dict()

        # update property in dict
        resourceVars[varProperty]=varValue

        # write the vars file back
        jsonResourceVarsData=json.dumps(resourceVars,indent=4)
        with open(serviceRootVarsPath, 'w', encoding='utf-8') as f:
            f.write( jsonResourceVarsData )
        return(0)

    def createSubObjects(self, rfr):
        #create the in-memory resources based on the RfResource class, classes defined below
        #create service root sub-objects
        self.serviceVersions=self.RfServiceVersions(rfr,"base","static","RedfishVersions.json")
        self.redDrumServiceInfo=self.RfRedDrumInfo(rfr,"base","static","RedDrumInfo.json")
        self.odata=self.RfOdataServiceDocument(rfr,"base","static","OdataServiceDocument.json")
        self.metadata=self.RfMetadataDocument(rfr,"base","static","ServiceMetadata.xml",contentType="xml")

        #create the sessionService, AccountService and EventService classes
        self.sessionService=RfSessionService(rfr)
        self.accountService=RfAccountService(rfr)
        self.eventService=RfEventService(rfr)

        #create the JsonSchemas and Registries classes
        self.jsonSchemas = RfJsonSchemas(rfr)
        self.registries  = RfRegistries(rfr)

        #create the three data resource
        # v2.x.x of RedDrum-Frontend no longer caches chassis, managers, and systems
        #  self.chassis=RfChassisResource(rfr)
        #  self.managers=RfManagersResource(rfr)
        #  self.systems=RfSystemsResource(rfr)


    def finalInitProcessing(self,rdr):
        self.hdrs=RfAddHeaders(rdr)
        rdr.logMsg("INFO","RedDrum Redfish Service Fronend Initialization Complete:\n{}".format(self.resData['Name']))


    # GET service root resource
    def getResource(self, request):
        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.resData, allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)
        response=json.dumps(self.resData,indent=4)
        return(0,200,"",response,hdrs)

    class RfServiceVersions(RfStaticResource):
        pass
    
    class RfRedDrumInfo(RfStaticResource):
        pass

    class RfOdataServiceDocument(RfStaticResource):
        pass

    class RfMetadataDocument(RfStaticResource):
        pass


    def updateResourceCache(self,rdr,rdata):
        # xg99 need to complete as part of hotplug
        # rdata is dict of form: { "Id" "<id>" }  where <id> is of form: "Rack1-Block2-Sled3-Node1"
        if "Id" in rdata:
            resourceId=rdata["Id"] 
        else:
            rdr.logMsg("WARNING", "updateResourceCache: bad input. No Id property in request")
            return(4,400,"Bad Input, No Id Property","")

        rdr.logMsg("INFO", "updateResourceCache:  got request to update resource: {}".format(resourceId)) 
        #xg99 implement later with hotplug
        return(0,204,"","")



    # clearAccountsCaches is called from FrontEnd to clear AccountService and SessionsService caches
    #     rdata  is of form:   { "ClearOn": <val> }  where <val> is oneOf{"Restart","Now"}
    def clearAccountsCaches(self,rdr,rdata):
        if "ClearOn" in rdata:
            clearOn=rdata["ClearOn"] 
        else:
            rdr.logMsg("ERROR", "clearAccountsCaches: bad input. No ClearOn property in request")
            return(4,400,"Bad Input, No ClearOn Property","")

        if clearOn=="Restart":
            rdr.logMsg("INFO", "Clearing Frontend Accounts persistent caches on next restart.")

            # Set persistent flag in file ServiceRootVars file to clear Account Caches on next restart 
            setServiceRootVars(rdr, "ClearAccountsCaches", True )

            return(0,204,"","")

        elif clearOn=="Now" or clearOn=="Startup":
            rdr.logMsg("INFO", "Clearing Accounts and SessionService Cache Data. ClearOn: {}".format(clearOn)) 

            # first clear db caches for SessionService 
            self.sessionService.clearSessionServiceDatabaseFiles(self,rdr)

            # then clear db caches for users, roles, and AccountsService
            self.accountService.clearAccountServiceDatabaseFiles(self,rdr)

            # then clear db caches for users, roles, and AccountsService
            self.eventService.clearEventServiceDatabaseFiles(self,rdr)

            return(0,204,"","")
        else:
            rdr.logMsg("ERROR", "clearAccountsCaches got bad input. ClearOn: {}".format(clearOn)) 
            return(4,400,"Bad Input, Invalid ClearOn Property value","")
        return(6,500,"","")


    # clearHwResourceCaches is called from g5StartupDiscovery Backend with "ClearOn"="Now"
    #     or called from FrontEnd with "ClearOn"= either "Now" or "Restart" or from statup with val: Starup
    #     rdata  is of form:   { "ClearOn": <val> }  where <val> is oneOf{"Restart","Now"}
    def clearHwResourceCaches(self,rdr,rdata):
        if "ClearOn" in rdata:
            clearOn=rdata["ClearOn"] 
        else:
            rdr.logMsg("WARNING", "clearHwResourceCaches: bad input. No ClearOn property in request")
            return(4,400,"Bad Input, No ClearOn Property","")

        if clearOn=="Restart":
            rdr.logMsg("INFO", "Clearing Frontend Resource persistent caches on next Restart")

            # Set persistent flag in file ServiceRootVars file to clear Resource Caches on next restart 
            setServiceRootVars(rdr, "ClearHwResourceCaches", True )
            return(0,204,"","")

        elif clearOn=="Now" or clearOn=="Startup":
            rdr.logMsg("INFO", "Clearing Frontend Resource persistent caches. ClearOn: {}".format(clearOn))
            #self.chassis.clearChassisResourceCaches(rdr)
            #self.managers.clearManagersResourceCaches(rdr)
            #self.systems.clearSystemsResourceCaches(rdr)
            return(0,204,"","")
        else:
            rdr.logMsg("WARNING", "clearHwResourceCaches got bad input. ClearOn: {}".format(clearOn)) 
            return(4,400,"Bad Input, Invalid ClearOn Property value","")
        return(6,500,"","")



    # clearUuidCache is called from front end to clear the uuid cache
    #     rdata  is of form:   { "ClearOn": <val> }  where <val> is oneOf{"Restart" }
    def clearUuidCache(self,rdr,rdata):
        if "ClearOn" in rdata:
            clearOn=rdata["ClearOn"] 
        else:
            rdr.logMsg("WARNING", "clearUuidCache: bad input. No ClearOn property in request")
            return(4,400,"Bad Input, No ClearOn Property","")

        if clearOn=="Restart":
            rdr.logMsg("INFO", "Clearing Uuid Resource persistent caches on next Restart")

            # Set persistent flag in file ServiceRootVars file to clear Resource Caches on next restart 
            setServiceRootVars(rdr, "ClearUuid", True )
            return(0,204,"","")

        else:
            rdr.logMsg("WARNING", "clearUuidCache got bad input. ClearOn: {}".format(clearOn)) 
            return(4,400,"Bad Input, Invalid ClearOn Property value","")
        return(6,500,"","")

