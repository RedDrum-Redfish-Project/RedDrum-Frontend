
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import time
import sys
import re
import string
#from .rootData import RfRoot
from .redfish_headers import RfAddHeaders
from enum import Enum
from .generateId import rfGenerateId

# TODO shouldn't this be moved to the "Event" class???
class EventType(Enum):
    statusChange = "StatusChange"
    resourceUpdated = "ResourceUpdated"
    resourceAdded = "ResourceAdded"
    resourceRemoved= "ResourceRemoved"
    alert = "Alert"
    

class RfEventService():  
    # Note that this resource was created in serviceRoot for the Account service.
    def __init__(self,rdr ):
        #TODO kill rdr references
        self.rdr=rdr
        self.loadResourceTemplates(rdr )
        self.loadEventServiceDatabaseFiles(rdr )
        self.initializeSubscriptionsDict(rdr)
        self.hdrs=RfAddHeaders(rdr)

    def loadResourceTemplates( self, rdr ):
        #load AccountService Template
        self.eventServiceTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventService.json")

        #load Accounts Collection Template
        self.subscriptionsTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventDestinationCollection.json")

        #load Account Entry Template
        #self.accountEntryTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "ManagerAccount.json")

        #load Roles Collection Template
        #self.rolesCollectionTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "RoleCollection.json")

        #load Roles Entry Template
        self.EventSubscriptionTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventDestination.json")

    # worker function called by loadResourceTemplates() to load a specific template
    # returns a dict loaded of the template file, which calling function saves to a variable
    # if file does not exist, the service exits
    #    assumes good json in the template file
    def loadResourceTemplateFile( self, dataPath, subDir, filename ):
        indxFilePath=os.path.join(dataPath, subDir, filename)
        if os.path.isfile(indxFilePath):
            response=json.loads( open(indxFilePath,"r").read() )
            return(response)
        else:
            self.rdr.logMsg("CRITICAL", 
               "*****ERROR: EventService: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)
        
    def loadEventServiceDatabaseFiles(self, rdr ):
        # load the EventService database file:      "EventServiceDb.json"
        filename="EventServiceDb.json"
        self.eventServiceDbFilePath,self.eventServiceDb=self.loadDatabaseFile(rdr,"db",filename) 

        # load the Events collection database file: "EventsDb.json"
        filename="EventDestinationCollectionDb.json"
        self.subscriptionsDbFilePath,self.subscriptionsDb=self.loadDatabaseFile(rdr,"db",filename) 

        # load the Roles collection  database file:     "RolesDb.json"
        filename="EventDestinationDb.json"
        self.rolesDbFilePath,self.rolesDb=self.loadDatabaseFile(rdr,"db",filename) 

    # worker function called by loadEventServiceDatabaseFiles() to load a specific database file
    # returns two positional parameters:
    #    the database filepath,
    #    a dict of the database file
    # if file does not exist in the varDataPath/subDir directory (the database dir), 
    #   then it loads the file from baseDataBath (the default database), and saves it back to the varDataPath dir
    # assumes good json in the database file
    def loadDatabaseFile( self, rdr, subDir, filename ):
        dbFilePath=os.path.join(rdr.varDataPath,subDir, filename)
        if os.path.isfile(dbFilePath):
            dbDict=json.loads( open(dbFilePath,"r").read() )
        else:
            self.rdr.logMsg("INFO","*****WARNING: Json Data file:{} Does not exist. Creating default.".format(dbFilePath))
            # read the data in from the default database dir with the rm-tools package
            dfltDbFilePath=os.path.join(rdr.baseDataPath,subDir,filename)
            if os.path.isfile(dfltDbFilePath):
                dbDict=json.loads( open(dfltDbFilePath,"r").read() )
            else:
                self.rdr.logMsg("CRITICAL", 
                    "*****ERROR: Default Json Database file:{} Does not exist. Exiting.".format(dfltDbFilePath))
                sys.exit(10)
            #write the data back out to the var directory where the dynamic db info is kept
            dbDictJson=json.dumps(dbDict,indent=4)
            with open( dbFilePath, 'w', encoding='utf-8') as f:
                f.write(dbDictJson)
        # return path and data
        return(dbFilePath,dbDict)

    def clearEventServiceDatabaseFiles(self, rdr ):
        # clear the AccountService database file:      "AccountServiceDb.json"
        filename="EventServiceDb.json"
        self.eventServiceDb=self.clearDatabaseFile(rdr,"db",filename) 

        # clear the Accounts collection database file: "AccountsDb.json"
        filename="EventDestinationCollectionDb.json"
        self.subscriptionsDb=self.clearDatabaseFile(rdr,"db",filename) 

        # clear the Roles collection  database file:     "RolesDb.json"
        filename="EventDestinationDb.json"
        self.rolesDb=self.clearDatabaseFile(rdr,"db",filename) 

#TODO look at how chassis does the clear and follow
    def clearDatabaseFile( self, rdr, subDir, filename ):
        clearedDb=dict()
        dbFilePath=os.path.join(rdr.varDataPath,subDir, filename)
        #write the data back out to the var directory where the dynamic db info is kept
        #dbDictJson=json.dumps(clearedDb,indent=4)
        #with open( dbFilePath, 'w', encoding='utf-8') as f:
        #        f.write(dbDictJson)
        if os.path.exists(dbFilePath):
            os.remove(dbFilePath)
        # return path and data
        return(clearedDb)
# Implementing 
# Redfish.required is only for standard
# Intel RSD may have additional required may have other types of requirement
# Intel RSD is proprietary but eventually back into RFStandard
# Concept of profiles describe additional requirements for a particular use-case
# Example is OCP: HW Spec map to RF Property/Resources
# RFImplementation - Profiles/Text in a spec

# Annotations in payloads; 
# Odata whitepaper spec
# Property @ is an annotation
# Redfish Service Validator

#TODO add properties for Subscription retry
    def initializeSubscriptionsDict(self,rdr):
        # this is the in-memory database of eventDestination properties that are not persistent
        # the eventDestinationCollectionDict is a dict indexed by   eventDestinationCollectionDict[accountid][<nonPersistentAccountParameters>]
        #   self.eventDestinationCollectionDict[eventdestinationid]=
        #       { "Locked": <locked>,  "FailedLoginCount": <failedLoginCnt>, "LockedTime": <lockedTimestamp>,
        #         "AuthFailTime": <authFailTimestamp> }
        self.subscriptionsDict=dict() #create an empty dict of EventDestination entries
        curTime=time.time()

        #create the initial state of the eventDestinationCollectionDict from the eventDestinationCollectionDb
        #for subscription in eventSubscriptionDb:
        for eventSubscription in self.subscriptionsDb:
        #Change properties that reflect evenSubscription resources
            self.subscriptionsDict[eventSubscription]={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }
        

    # Stub response for unimplemented API's
    def stubResponse(self):
        rc=1
        statusCode=501
        errString="Not Implemented--Work In Progress"
        resp=""
        hdrs={}
        return(rc,statusCode,errString,resp,hdrs)

            
    # GET EventService
    def getEventServiceResource(self,request):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.eventServiceTemplate, allow="GetPatch")

        # Process HEAD method
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # create a copy of the EventService resource template 
        resData2=dict(self.eventServiceTemplate)

        # add required properties
        resData2["@odata.id"] = "/redfish/v1/EventService"
        resData2["Id"] = "EventService"
        resData2["Name"] = "Event Service"
        resData2["ServiceEnabled"]  = True

        # Health
        #TODO change static entries to read from DB

        resData2["Status"]  = dict()
        resData2["Status"]["Health"] = self.eventServiceDb["Status"]["Health"] #e.g. "OK"
        resData2["Status"]["State"] = self.eventServiceDb["Status"]["State"] #e.g. "Enabled"

        # Retry
        resData2["DeliveryRetryAttempts"] = self.eventServiceDb["DeliveryRetryAttempts"] #e.g. "3"
        resData2["DeliveryRetryIntervalSeconds"] = self.eventServiceDb["DeliveryRetryIntervalSeconds"] #e.g. "60"

        # Event Types #TODO Enum?
        resData2["EventTypesForSubscription"]  = ["StatusChange", "ResourceAdded", "ResourceUpdated", "ResourceRemoved", "Alert"]
            
        # Subscriptions
        resData2["Subscriptions"] = { "@odata.id": "/redfish/v1/EventService/Subscriptions" }

        # Action (SubmitTestEvent)
        # odata.context?
        # etc?

        # create the response json data and return
        resp=json.dumps(resData2,indent=4)
        return(0, 200, "", resp, hdrs)

    # GET EventDestination Collection
    def getEventSubscriptionsResource(self, request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"],
                                     resource=self.subscriptionsTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # the routine copies a template file with the static redfish parameters
        # then it updates the dynamic properties from the EventDestinationDb dict
        # for EventDestinationCollection GET, we build the Members array

        # copy the EventDestinationCollection template file (which has an empty EventDestination array)
        resData2=dict(self.subscriptionsTemplate)
        count=0
        # now walk through the entries in the EventDestinationDb and build the EventDestinationCollection Members array
        # note that the members array is an empty array in the template
        eventDestinationUriBase="/redfish/v1/EventService/Subscriptions/"
        for eventDestinationid in self.subscriptionsDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=eventDestinationUriBase + eventDestinationid
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            resData2["Members"] = resData2["Members"] + newMember
        resData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(resData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)

    # GET subscription Entry
    def getSubscriptionEntry(self, request, subscriptionId):

        # First verify that the subscriptionId is valid
        if subscriptionId not in self.subscriptionsDb:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "",errhdrs)

        # generate header info depending on the specific subscriptionId
        # predefined subscriptions cannot be deleted or modified
        #     self.subscriptionsDb[subscriptionId]={"Name": subscriptionname, "Description": subscriptionDescription, "IsPredefined": idPredefined, 
        #                       "AssignedPrivileges": privileges }
        if self.subscriptionsDb[subscriptionId]["IsPredefined"] is True:
            # pre-defined subscriptions cannot be deleted or modified
            allowMethods="Get"
        else:
            allowMethods=["HEAD","GET","PATCH","DELETE"],
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
                                     resource=self.subscriptionEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # copy the template subscriptionEntry resource
        resData2=dict(self.subscriptionEntryTemplate)

        # now overwrite the dynamic data from the subscriptionsDb 
        subscriptionEntryUri="/redfish/v1/EventService/Subscriptions/" + subscriptionId
        resData2["@odata.id"]=subscriptionEntryUri
        resData2["Id"]=subscriptionId
        resData2["Name"]=self.subscriptionsDb[subscriptionId]["Name"]
        resData2["Description"]=self.subscriptionsDb[subscriptionId]["Description"]
        resData2["IsPredefined"]=self.subscriptionsDb[subscriptionId]["IsPredefined"]
        resData2["AssignedPrivileges"]=self.subscriptionsDb[subscriptionId]["AssignedPrivileges"]
        if "subscriptionId" in self.subscriptionsDb[subscriptionId]:
            resData2["subscriptionId"]=self.subscriptionsDb[subscriptionId]["subscriptionId"]
        else:
            resData2["subscriptionId"]=subscriptionId

        # convert to json
        jsonResponseData=(json.dumps(resData2,indent=4))

        return(0, 200, "", jsonResponseData, respHdrs)




### Generate each subscription with ids example for POST ###
#SessionService/postSessionResource
#rfGenerateId generateId do not use S or A

# Questions:
# Is service / object patchable/puttable/etc
# How indicated patchable/puttable properties

### for PATCH/POST/ETC ###
# check mockups on dmtf to see things like how numbers are generated for subscription ID
# check xml schemas on dmtf github for sanity checking of required values (RequiredOnCreate)
# Do we reject if uneeded data?  Probably not
# check values are sane, regexp, integers versus strings, etc
### for PATCH/POST/ETC ###

    # PATCH EventService
    def patchEventServiceResource(self,request, patchData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # First check only patchable properties are present
        patchable=("DeliveryRetryAttempts","DeliveryRetryIntervalSeconds")

        for prop in patchData:
            if not prop in postables:
                return (4, 400, "Bad Request-Invalid Post Property Received", "",errhdrs)

        if( (patchData['DeliveryRetryAttempts'] is None) or (patchData['DeliveryRetryIntervalSeconds'] is None)):
            return (4, 400, "Bad Request-No patchable properties received", "",errhdrs)

        dlvyRtryAttempts=None
        dlvyRtryIntvlSecs=None
        

        ##########################################
        # now verify that the Post data is valid #
        ##########################################

        #TODO is this an integer and bounds checking???
        #if dlvyRtryAttempts is not an integer and too big...
        #dlvyRtryIntvlSecs is not an integer and too big...
        # then convert the patch properties passed-in to integers
        for key in patchData:
            newVal=patchData[key]
            try:
                numVal=round(newVal)
            except ValueError:
                return(4,400,"invalid value","",hdrs)
            else:
                patchData[key]=numVal

        # then verify the properties passed-in are in valid ranges
        #newDuration=self.accountServiceDb["AccountLockoutDuration"]
        #newResetAfter=self.accountServiceDb["AccountLockoutCounterResetAfter"]
        if("DeliveryRetryAttempts" in patchData):
            dlvyRtryAttempts=patchData['DeliveryRetryAttempts']
        if("DeliveryRetryIntervalSeconds" in patchData):
            dlvyRtryIntvlSecs=patchData['DeliveryRetryIntervalSeconds']

        # Todo what is legal values???
        if( newDuration < newResetAfter ):
            return(4,400,"Bad Request-Invalid value","",hdrs)
        # if here, all values are good. Update the eventServiceDb dict
        for key in patchData:
            self.eventServiceDb[key]=patchData[key]

        # write the data back out to the eventService database file
        eventServiceDbJson=json.dumps(self.eventServiceDb,indent=4)
        with open( self.eventServiceDbFilePath, 'w', encoding='utf-8') as f:
            f.write(eventServiceDbJson)
        return(0, 204, "", "", hdrs)


    # POST Subscription
    # POST to Subscription collection  (add subscription)
    def postSubscriptionResource(self,request, postData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # First check that all required on create properties were sent as post data
        if( (postData['EventDestination'] is None) or (postData['EventTypes'] is None) or (postData['Protocol'] is None ) ):
            return (4, 400, "Bad Request-Required On Create properties not all sent", "",errhdrs)

        context=None
        protocol=None
        eventDestination=None
        eventTypes=None

        if("Context" in postData):
            context=postData['Context']

        if("Protocol" in postData):
            protocol=postData['Protocol']

        if("EventDestination" in postData):
            eventDestination=postData['EventDestination']

        if("EventTypes" in postData):
            eventTypes=postData['EventTypes']


        # Next verify that the client didn't send us a property we cant write when creating the event
        # we need to fail the request if we cant handle any properties sent
        # TODO Add httpheaders?
        postable=("Context","Protocol","EventDestination","EventTypes")
        for prop in postData:
            if not prop in postables:
                return (4, 400, "Bad Request-Invalid Post Property Sent", "",errhdrs)

        ##########################################
        # now verify that the Post data is valid #
        ##########################################

        # 'Redfish' is the only protocol supported
        if (protocol != 'Redfish'):
            return (4, 400, "Bad Request-Only the 'Redfish' protocol is supported", "",errhdrs)

        # TODO eventDestination must be of the form (URL/URI) http:// 

        #if (eventDestination != 

        # https://docs.python.org/2/library/urlparse.html
        # https://codereview.stackexchange.com/questions/19663/http-url-validating
#        regex = re.compile(
#    r'^(?:http|ftp)s?://' # http:// or https://
#    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
#    r'localhost|' # localhost...
#    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
#    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
#    r'(?::\d+)?' # optional port
#    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


        # eventTypes must exist in the collection Event.EventType enum
        # TODO in reality, we only support 3 event types...
        for event in eventTypes:
            if not event in EventType.__members__:
                return (4, 400, "Bad Request-Supported EventType not sent", "",errhdrs)

        if not isinstance(context, basestring):
            return (4, 400, "Bad Request-Context must be a string", "",errhdrs)

        # create response header data
        subscriptionId=rfGenerateId(leading="E",size=8)
        locationUri="/redfish/v1/EventService/Subscriptions/" + subscriptionId

        # TODO add correct data ; add the new subscription entry to the eventDestinationCollectionDb
        self.eventDestinationCollectionDb[subscriptionId]={"UserName": username, "Password": password, 
                  "RoleId": roleId, "Enabled": enabled, "Deletable": True}

        # add the new event entry to the eventsDict
        dfltEventDictEntry={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }
        self.eventsDict[subscriptionId]=dfltEventDictEntry

        # write the EventDb back out to the file
        dbFilePath=os.path.join(self.rdr.varDataPath,"db", "EventsDb.json")
        dbDictJson=json.dumps(self.eventDestinationCollectionDb, indent=4)
        with open( dbFilePath, 'w', encoding='utf-8') as f:
            f.write(dbDictJson)
        
        # get the response data
        rc,status,msg,respData,respHdr=self.getEventEntry(request, subscriptionId)
        if( rc != 0):
            #something went wrong--return 500
            return(5, 500, "Error Getting New Event Data","",{})

     ## Not required
        # calculate eTag
        #etagValue=self.calculateEventEtag(subscriptionId)

        # get the response Header with Link, and Location
        #respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri,
        #                             resource=self.eventEntryTemplate, strongEtag=etagValue)
        respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri,
                                     resource=self.eventEntryTemplate)

        #return to flask uri handler
        return(0, 201, "Created",respData,respHeaderData)

# PATCH Subscription
    def patchSubscriptionEntry(self, request, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        #first verify client didn't send us a property we cant patch
        patchables=("Context")

        if("Context" in postData):
            context=patchData['Context']

        if not isinstance(context, basestring):
            return (4, 400, "Bad Request-Context must be a string", "",errhdrs)

        for key in patchData:
            if( not key in patachables ):
                return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)

        #TODO is locationUri null?
        respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri, resource=self.eventEntryTemplate)

        #return to flask uri handler
        return(0, 201, "Created",respData,respHeaderData)

 # Test Event Subscription
    def postPutEventTestEntry(self, request, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        #first verify client didn't send us a property we cant patch
        patchables=("Context")

        if("Context" in postData):
            context=patchData['Context']

        if not isinstance(context, basestring):
            return (4, 400, "Bad Request-Context must be a string", "",errhdrs)

        for key in patchData:
            if( not key in patachables ):
                return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)

        #TODO is locationUri null?
        respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri, resource=self.eventEntryTemplate)

        #return to flask uri handler
        return(0, 201, "Created",respData,respHeaderData)
   
       
        #
#    # getAccountAuthInfo(username,password)
#    #   returns: rc, errMsgString, accountId, roleId, userPrivileges
#    #      rc=404 if username is not in eventDestinationCollectionDb
#    #      rc=401 if username is invalid or mismatches password, or account is locked or not enabled
#    #        =0   if authenticated
#    #   self.accountsDict[accountid]={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }
#



#
#    # ------------Accounts Collection Functions----------------
#
#
#    # GET Accounts Collection
#    def getAccountsCollectionResource(self, request ):
#        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"],
#                                     resource=self.eventDestinationCollectionTemplate)
#        if request.method=="HEAD":
#            return(0,200,"","",hdrs)
#
#        # the routine copies a template file with the static redfish parameters
#        # then it updates the dynamic properties from the eventDestinationCollectionDb and accountsDict
#
#        # copy the eventDestinationCollection template file (which has an empty accounts array)
#        resData2=dict(self.eventDestinationCollectionTemplate)
#        count=0
#        # now walk through the entries in the eventDestinationCollectionDb and built the eventDestinationCollection Members array
#        # note that the template starts out an empty array
#        accountUriBase="/redfish/v1/AccountService/Accounts/"
#        for accountEntry in self.eventDestinationCollectionDb:
#            # increment members count, and create the member for the next entry
#            count=count+1
#            memberUri=accountUriBase + accountEntry
#            newMember=[{"@odata.id": memberUri}]
#
#            # add the new member to the members array we are building
#            resData2["Members"] = resData2["Members"] + newMember
#
#        resData2["Members@odata.count"]=count
#
#        # convert to json
#        jsonResponseData2=json.dumps(resData2,indent=4)
#
#        return(0, 200, "",  jsonResponseData2, hdrs)
#
#
#    # GET Account Entry
#    def getAccountEntry(self, request, accountid):
#        # verify that the accountId is valid
#        if accountid not in self.eventDestinationCollectionDb:
#            # generate error header for 4xx errors
#            errhdrs=self.hdrs.rfRespHeaders(request)
#            return(4, 404, "Not Found","",errhdrs)
#
#        # first just copy the template sessionEntry resource
#        resData=dict(self.accountEntryTemplate)
#
#        # generate header info depending on the specific accountid
#        #    accounts with property "Deletable"=False cannot be deleted
#        #    for RedDrum, this includes accountid "root"
#        #    for reference:   self.eventDestinationCollectionDb[accountid]=
#        #          {"UserName": username,    "Password": password, 
#        #          "RoleId": roleId,    "Enabled": enabled,    "Deletable": True}
#        if self.eventDestinationCollectionDb[accountid]["Deletable"] is False:
#            allowMethods="GetPatch"
#        else:
#            allowMethods=["HEAD","GET","PATCH","DELETE"]
#
#        # check if account was locked but has now exceeded LockoutDuration
#        #    if so, then unlock before returning data
#        curTime=time.time()
#        if self.accountsDict[accountid]["Locked"] is True:
#            if( (curTime - self.accountsDict[accountid]["LockedTime"]) > self.eventServiceDb["AccountLockoutDuration"] ):
#                # the lockout duration has expired.   unlock it.
#                self.accountsDict[accountid]["Locked"]=False
#                self.accountsDict[accountid]["LockedTime"]=0
#                self.accountsDict[accountid]["FailedLoginCount"]=0
#                self.accountsDict[accountid]["AuthFailTime"]=0
#
#        # now overwrite the dynamic data from the eventDestinationCollectionDb
#        accountUri="/redfish/v1/AccountService/Accounts/" + accountid
#        accountRoleId=self.eventDestinationCollectionDb[accountid]["RoleId"]
#        resData["@odata.id"]=accountUri
#        resData["Id"]=accountid
#        resData["Name"]="UserAccount"
#        resData["Description"]="Local Redfish User Account"
#        resData["Enabled"]=self.eventDestinationCollectionDb[accountid]["Enabled"]
#        resData["Password"]=None   # translates to Json: null
#        resData["UserName"]=self.eventDestinationCollectionDb[accountid]["UserName"]
#        resData["RoleId"]=accountRoleId
#        roleUri="/redfish/v1/AccountService/Roles/" + accountRoleId
#        resData["Links"]={ "Role": {} }
#        resData["Links"]["Role"]["@odata.id"]=roleUri
#
#        # now overwrite the dynamic data from the sessionsDict
#        # this is non-persistent account data
#        resData["Locked"]=self.accountsDict[accountid]["Locked"]  
#
#        # calculate eTag
#        etagValue=self.calculateAccountEtag(accountid)
#
#        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
#                                     resource=self.accountEntryTemplate, strongEtag=etagValue)
#        if request.method=="HEAD":
#            return(0,200,"","",respHdrs)
#
#        # convert to json
#        jsonResponseData=json.dumps(resData,indent=4)
#
#        #return etagHeader in response back to URI processing.  It will merge it
#        return(0, 200, "",jsonResponseData, respHdrs)
#
#

#
#
#
# DELETE Subscription
#    # delete the Subscription
#    # all we have to do is verify the subscriptionid is correct--
#    # and then, if it is valid, delete the entry for that subscriptionid from the eventDestinationCollectionDb and subscriptionsDict
    def deleteSubscriptionEntry(self, request, subscriptionid):
        hdrs=self.hdrs.rfRespHeaders(request)
        # generate the headers

        # First, verify that the subscriptionid is valid, 
        if subscriptionid not in self.eventDestinationCollectionDb:
            return(4, 404, "Not Found","",hdrs)

        # check if this is a deletable subscription
        if "Deletable" in self.eventDestinationCollectionDb[subscriptionid]:
            if self.eventDestinationCollectionDb[subscriptionid]["Deletable"] is True:
                del self.eventDestinationCollectionDb[subscriptionid]
            else:
                # get allow headers
                resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="GetPatch" )
                return(4, 405, "Method Not Allowed for this Subscription/URI","",resp405Hdrs)

        # delete the subscriptionid entry from the subscriptionsDict also
        if subscriptionid in self.subscriptionsDict:
            del self.subscriptionsDict[subscriptionid]

        # write the data back out to the eventService database file
        eventDestinationCollectionDbJson=json.dumps(self.eventDestinationCollectionDb,indent=4)
        filename="SubscriptionsDb.json"
        with open( self.eventDestinationCollectionDbFilePath, 'w', encoding='utf-8') as f:
            f.write(eventDestinationCollectionDbJson)

        return(0, 204, "No Content","",hdrs)
#
#    # Patch Account
#    # patch an Account Entry 
#    # used to update password or roleId, or unlock, or enable/disable the account
#    #   self.accountsDict[accountid]=
#    #       { "Locked": <locked>,  "FailedLoginCount": <failedLoginCnt>, "LockedTime": <lockedTimestamp>,
#    #         "AuthFailTime": <authFailTimestamp> }
#    def patchAccountEntry(self, request, accountid, patchData):
#        # generate headers for 4xx error messages
#        errhdrs = self.hdrs.rfRespHeaders(request )
#
#        # First, verify that the accountid is valid, 
#        if accountid not in self.eventDestinationCollectionDb:
#            return(4, 404, "Not Found", "", errhdrs)
#
#        # 2nd if Password is in patch data, make sure that the request used https, or that credential update over http was enabled
#        if "Password" in patchData:
#            # procesa special cases for request coming in over http or https based on RedDrum.conf auth config settings
#            requestHeadersLower = {k.lower() : v.lower() for k,v in request.headers.items()}
#            #print("EEEEEEEE: hdrs: {}".format(requestHeadersLower))
#            #if "X-rm-from-rproxy" in requestHeadersLower and requestHeadersLower["x-rm-from-rproxy"]=="https":
#            if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTPS":
#                # case: scheme is https,  so execute the API
#                pass
#            elif self.rdr.RedfishAllowUserCredUpdateOverHttp is True:
#                # case: scheme=http,  but credential update over Http is allowed 
#                pass
#            else:
#                # case: scheme=http, credential update over http is NOT allowed
#                #  so return a 404-Not Found  status code
#                return(4, 404, "404-Not Found-URI not supported over http", "", errhdrs)
#
#        # verify that the patch data is good
#
#        # first verify that ALL of the properties sent in patch data are patchable for redfish spec
#        patchables=("Password","RoleId","Locked","Enabled","UserName")
#        for prop in patchData:
#            if( not prop in patchables ):
#                return (4, 400, "Bad Request-one or more properties not patchable", "", errhdrs)
#
#        # verify privilege is sufficient to change this property
#        #    Privilege "ConfigureSelf" allows a user to change THEIR password, but no other property
#        #    Privilege "ConfigureUsers" is required to change other users passwords
#
#        # note that if "Password" is in patchData:
#        # from auth wrapper, we know this user has either privilege ConfigureUsers or ConfigureSelf or both
#
#        # Define which properties can be patched with different privileges
#        #     Note: validPrivilegesList=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
#        if "ConfigureUsers" in self.currentUserPrivileges:
#            userHasPrivilegeToPatchProperties=["Password","RoleId","Locked","Enabled","UserName"]
#        elif (self.currentUserAccountId == accountid) and ("ConfigureSelf" in self.currentUserPrivileges):     
#            # user's accountId is same as target accountId and   the user that ConfigureSelf privilege to update their passwd
#            userHasPrivilegeToPatchProperties=["Password"]
#        else:  
#            userHasPrivilegeToPatchProperties=[]
#        
#        # check if user does not have sufficient privilege to set ANY of the properties in the patch data
#        # we must fail the ENTIRE patch if we can't update ANY of the properties
#        #     otherwise, per redfish spec, we would need to generate extended data detailing which properties cant be updated and why
#        for prop in patchData:
#            if prop not in userHasPrivilegeToPatchProperties:
#                self.rdr.logMsg("WARNING",
#                   "403 Unauthorized-Patch Account: User does not have privilege to update account prop: {}".format(prop))
#                return (4, 403, "User does not have privilege to update account data", "", errhdrs)
#
#        # verify that the etag requirements are met
#        # if request header had an If-Match: <etag>, verify the etag is still valid
#        doIfMatchEtag=False
#        if request.headers.get('if-match') is True:
#            requestEtag = request.headers["if-match"]
#            doIfMatchEtag=True
#
#        if doIfMatchEtag is True:
#            # first calculate strong eTag for this account
#            currentEtag='"' + self.calculateAccountEtag(accountid) + '"'
#            # verify they match
#            if requestEtag  != currentEtag:
#                self.rdr.logMsg("WARNING","412 If-Match Condition Failed-Patch Account")
#                return (4, 412, "If-Match Condition Failed", "", errhdrs)
#
#        # if Password was in patchData, verify value is good 
#        if "Password" in patchData:
#            password=patchData["Password"]
#            # check if password length is less than value set in eventService MinPasswordLength
#            if "MinPasswordLength" in self.eventServiceDb:
#                if len(password) < self.eventServiceDb["MinPasswordLength"]:
#                    self.rdr.logMsg("WARNING","400 Bad Request-Patch Account: Password length less than min")
#                    return (4, 400, "Bad Request-Password length less than min", "", errhdrs)
#            if "MaxPasswordLength" in self.eventServiceDb:
#                if len(password) > self.eventServiceDb["MaxPasswordLength"]:
#                    self.rdr.logMsg("WARNING","400 Bad Request-Patch Account: Password length exceeds max")
#                    return (4, 400, "Bad Request-Password length exceeds max", "", errhdrs)
#
#            # check if password meets regex requirements---no whitespace or ":"
#            passwordMatchPattern="^[^\s:]+$"
#            passwordMatch = re.search(passwordMatchPattern, password)
#            if not passwordMatch:
#                self.rdr.logMsg("WARNING","400 Bad Request-Patch Account: invalid password: whitespace or : is not allowed")
#                return (4, 400, "Bad Request-invalid password-whitespace or : is not allowed", "", errhdrs)
#
#            # generate the password hash
#            # for sha512, this creates string like: "$6$R53DEEDrreeesg$REEDD/esEEFereg"  ie "$6$<salt>$<hash>"
#            passwdHash = self.cryptContext.hash(password) 
#
#        # if roleId was in patchData, verify value is good 
#        if "RoleId" in patchData: 
#            foundRoleId=False
#            for roleid in self.rolesDb:
#                if "RoleId" in self.rolesDb[roleid]:
#                    thisRoleIdName = self.rolesDb[roleid]["RoleId"]
#                else:
#                    thisRoleIdName = roleId  # early Redfish model before RoleId prop existed in Roles
#                # check if the specified roleId for the user matches one in the rolesDb 
#                if thisRoleIdName == patchData["RoleId"]:
#                    foundRoleId=True
#                    break
#
#            if foundRoleId is not True:
#                self.rdr.logMsg("WARNING","400 Bad Request-Patch Account: roleId does not exist")
#                return (4, 400, "Bad Request-roleId does not exist", "", errhdrs)
#
#        # check if Enabled is a boul
#        if "Enabled" in patchData: 
#            if (patchData["Enabled"] is not True) and (patchData["Enabled"] is not False):
#                self.rdr.logMsg("WARNING","400 Bad Request-Patch Account: Enabled must be either True or False")
#                return (4, 400, "Bad Request-Enabled must be either True or False", "", errhdrs)
#
#        # check if Locked is a legal value.   a user can only set locked to False, not true
#        if "Locked" in patchData: 
#            if patchData["Locked"] is not False:
#                self.rdr.logMsg("WARNING",
#                     "400 Bad Request-Patch Account: Locked can only be set to False by user")
#                return (4, 400, "Bad Request-Locked can only be set to False by user", "", errhdrs)
#
#        if "UserName" in patchData: 
#            badName=False
#            if ":" in patchData["UserName"]:
#                badName=True
#            for ch in patchData["UserName"]:
#                if ch in string.whitespace:
#                    badName=True
#            if badName is True:
#                self.rdr.logMsg("WARNING",
#                     "400 Bad Request-Patch Account: UserName cannot contait : or whitespace")
#                return (4, 400, "Bad Request-UserName cannot contain : or whitespace", "", errhdrs)
#
#        # if here, all values are good. Update the account dict
#        updateDb=False
#        for prop in patchData:
#            if (prop == "Locked"):
#                # save new value to the volatile accountsDict
#                self.accountsDict[accountid][prop]=patchData[prop]
#            else:
#                # save new value to the non-vol eventDestinationCollectionDb and update the Db cache file
#                updateDb=True
#                # if updating the password, save hash instead of cleartext passwd
#                if (prop == "Password"):
#                    self.eventDestinationCollectionDb[accountid][prop]=passwdHash
#                else:
#                    self.eventDestinationCollectionDb[accountid][prop]=patchData[prop]
#
#        # write the data back out to the eventService database file
#        if updateDb is True:
#            eventDestinationCollectionDbJson=json.dumps(self.eventDestinationCollectionDb,indent=4)
#            filename="AccountsDb.json"
#            with open( self.eventDestinationCollectionDbFilePath, 'w', encoding='utf-8') as f:
#                f.write(eventDestinationCollectionDbJson)
#
#        return(0, 204, "No Content","", errhdrs)
#
#    def postPutAccountEntry(self, request, accountid):
#        # the function returns a 405-Method not allowed
#        # the only processing here is to determine the proper Allow header to return
#        #   the specific Allow header list is a function of the accountid
#        #   some accounts are not deletable
#
#        if accountid not in self.eventDestinationCollectionDb:
#            # generate error header for 4xx errors
#            errhdrs=self.hdrs.rfRespHeaders(request)
#            return(4, 404, "Not Found","",errhdrs)
#
#        if self.eventDestinationCollectionDb[accountid]["Deletable"] is False:
#            allowMethods="GetPatch"
#        else:
#            allowMethods=["HEAD","GET","PATCH","DELETE"],
#        respHdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow=allowMethods)
#
#        return(0, 405, "Method Not Allowed","", respHdrs)

#    # ------------Roles Collection Functions----------------
#
#    # GET RolesCollection
#    # GET roles Collection
#    def getRolesCollectionResource(self, request):
#        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"],
#                                     resource=self.rolesCollectionTemplate)
#        if request.method=="HEAD":
#            return(0,200,"","",hdrs)
#
#        # the routine copies a template file with the static redfish parameters
#        # then it updates the dynamic properties from the rolesDb dict
#        # for RolesCollection GET, we build the Members array
#
#        # copy the rolesCollection template file (which has an empty roles array)
#        resData2=dict(self.rolesCollectionTemplate)
#        count=0
#        # now walk through the entries in the rolesDb and build the rolesCollection Members array
#        # note that the members array is an empty array in the template
#        roleUriBase="/redfish/v1/AccountService/Roles/"
#        for roleid in self.rolesDb:
#            # increment members count, and create the member for the next entry
#            count=count+1
#            memberUri=roleUriBase + roleid
#            newMember=[{"@odata.id": memberUri}]
#
#            # add the new member to the members array we are building
#            resData2["Members"] = resData2["Members"] + newMember
#        resData2["Members@odata.count"]=count
#
#        # convert to json
#        jsonRespData2=(json.dumps(resData2,indent=4))
#
#        return(0, 200, "", jsonRespData2, hdrs)
#
#
#    # GET Role Entry
#    def getRoleEntry(self, request, roleid):
#
#        # First verify that the roleId is valid
#        if roleid not in self.rolesDb:
#            # generate error header for 4xx errors
#            errhdrs=self.hdrs.rfRespHeaders(request)
#            return(4, 404, "Not Found", "",errhdrs)
#
#        # generate header info depending on the specific roleId
#        # predefined roles cannot be deleted or modified
#        #     self.rolesDb[roleid]={"Name": rolename, "Description": roleDescription, "IsPredefined": idPredefined, 
#        #                       "AssignedPrivileges": privileges }
#        if self.rolesDb[roleid]["IsPredefined"] is True:
#            # pre-defined roles cannot be deleted or modified
#            allowMethods="Get"
#        else:
#            allowMethods=["HEAD","GET","PATCH","DELETE"],
#        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
#                                     resource=self.EventDestinationTemplate)
#        if request.method=="HEAD":
#            return(0,200,"","",respHdrs)
#
#        # copy the template EventDestination resource
#        resData2=dict(self.EventDestinationTemplate)
#
#        # now overwrite the dynamic data from the rolesDb 
#        EventDestinationUri="/redfish/v1/AccountService/Roles/" + roleid
#        resData2["@odata.id"]=EventDestinationUri
#        resData2["Id"]=roleid
#        resData2["Name"]=self.rolesDb[roleid]["Name"]
#        resData2["Description"]=self.rolesDb[roleid]["Description"]
#        resData2["IsPredefined"]=self.rolesDb[roleid]["IsPredefined"]
#        resData2["AssignedPrivileges"]=self.rolesDb[roleid]["AssignedPrivileges"]
#        if "RoleId" in self.rolesDb[roleid]:
#            resData2["RoleId"]=self.rolesDb[roleid]["RoleId"]
#        else:
#            resData2["RoleId"]=roleid
#
#        # convert to json
#        jsonResponseData=(json.dumps(resData2,indent=4))
#
#        return(0, 200, "", jsonResponseData, respHdrs)
#
#
#    def postPutRoleEntry(self, request, roleid):
#        # the function returns a 405-Method not allowed
#        # the only processing here is to determine the proper Allow header to return
#        #   the specific Allow header list is a function of the roleid
#        #   some roles are not deletable or patchable
#
#        if roleid not in self.rolesDb:
#            # generate error header for 4xx errors
#            errhdrs=self.hdrs.rfRespHeaders(request)
#            return(4, 404, "Not Found", "",errhdrs)
#
#        if self.rolesDb[roleid]["IsPredefined"] is True:
#            # pre-defined roles cannot be deleted or modified
#            allowMethods="Get"
#        else:
#            allowMethods=["HEAD","GET","PATCH","DELETE"],
#        respHdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow=allowMethods)
#
#        return(0, 405, "Method Not Allowed","", respHdrs)
#
#def getAccountAuthInfo(self, username, password ):
#        authFailed=False
#        storedUsername=None
#        storedPassword=None
#        storedPrivileges=None
#        # if username or password is not None, it is an error
#        if username is None:
#            return(500, "Invalid Auth Check for username",None,None,None)
#        if password is None:
#            return(500, "Invalid Auth Check for password",None,None,None)
#
#        # from username, lookup accountId --- they are not necessarily the same
#        accountid=None
#        for acctid in self.eventDestinationCollectionDb:
#            if( username == self.eventDestinationCollectionDb[acctid]["UserName"] ):
#                accountid=acctid
#                break
#
#        # if we didn't find the username, return error
#        # since the username is invalid, we cant count invalid login attempts
#        if accountid is None:
#            return(404, "Not Found-Username Not Found",None,None,None)
#
#        # check if the account is disabled
#        if( self.eventDestinationCollectionDb[accountid]["Enabled"] is False ): 
#            return(401, "Not Authorized--Account Disabled",None,None,None)
#
#        # check if account was locked 
#        #    if it is locked but has now exceeded LockoutDuration then unlock and continue
#        #    if it is locked and not exceeded lockout duration, return 401 Not authorized
#        curTime=time.time()
#        if self.accountsDict[accountid]["Locked"] is True:
#            if( (curTime - self.accountsDict[accountid]["LockedTime"]) > self.eventServiceDb["AccountLockoutDuration"] ):
#                # the lockout duration has expired.   unlock it.
#                self.accountsDict[accountid]["Locked"]=False
#                self.accountsDict[accountid]["LockedTime"]=0
#                self.accountsDict[accountid]["FailedLoginCount"]=0
#                self.accountsDict[accountid]["AuthFailTime"]=0
#            else:
#                # lockout duration has not expired, return auth error
#                return(401, "Not Authorized--Account Locked By Service",None,None,None)
#
#        #the accountid exists, and account is enabled and not locked
#
#        #reset the AuthFailTime if time since last login failure is > AccountLockoutCounterResetAfter
#        authFailTime=self.accountsDict[accountid]["AuthFailTime"]
#        if( authFailTime != 0 ):
#            # if we have had failures and are counting authentication failures
#            resetAfterThreshold=self.eventServiceDb["AccountLockoutCounterResetAfter"]
#            if( ( curTime - authFailTime ) > resetAfterThreshold ):
#                # if time since last failure is greater than the reset counter threshold, then reset the counters
#                self.accountsDict[accountid]["AuthFailTime"]=0
#                self.accountsDict[accountid]["FailedLoginCount"]=0
#
#        #now check the associated password to see if authentication passis this time 
#        #check password
#        #xg11
#        #if( password != self.eventDestinationCollectionDb[accountid]["Password"] ): # TODO change to check hash
#        if self.cryptContext.verify(password, self.eventDestinationCollectionDb[accountid]["Password"]) is not True:
#            # authentication failed.
#
#            # check if lockout on authentication failures is enabled
#            lockoutThreshold=self.eventServiceDb["AccountLockoutThreshold"]
#            lockoutDuration=self.eventServiceDb["AccountLockoutDuration"]
#
#            # lockoutThreshold and lockoutDuration must BOTH be non-zero to enable lock on auth failures
#            if( (lockoutThreshold > 0) and (lockoutDuration > 0) ):
#                # check if we have now exceeded the login failures and need to lock the account
#                failedLoginCount=self.accountsDict[accountid]["FailedLoginCount"] + 1
#                if( failedLoginCount >= lockoutThreshold ):
#                    # lock the account and clear the AuthFailTime and FailedLogin counters
#                    self.accountsDict[accountid]["Locked"]=True
#                    self.accountsDict[accountid]["LockedTime"]=curTime
#                    self.accountsDict[accountid]["AuthFailTime"]=0
#                    self.accountsDict[accountid]["FailedLoginCount"]=0
#                    return(401, "Not Authorized--Password Incorrect and Account is now Locked By Service",None,None,None)
#                else:
#                    # we have not exceeded the failed authN threshold, update the counter and continue
#                    self.accountsDict[accountid]["FailedLoginCount"]=failedLoginCount
#                    self.accountsDict[accountid]["AuthFailTime"]=curTime
#                    return(401, "Not Authorized--Password Incorrect",None,None,None)
#
#            else:
#                # case where account lockout is not enabled
#                return(401, "Not Authorized--Password Incorrect",None,None,None)
#
#        #if here, the authentication was successful
#        #reset the lockout timers
#        self.accountsDict[accountid]["FailedLoginCount"]=0
#        self.accountsDict[accountid]["AuthFailTime"]=0
#
#        storedpassword=self.eventDestinationCollectionDb[accountid]["Password"]
#        storedRoleId=self.eventDestinationCollectionDb[accountid]["RoleId"]
#        storedPrivileges=self.rolesDb[storedRoleId]["AssignedPrivileges"]
#
#        # if here, all ok, return privileges
#        #   returns:  rc, errMsgString, userName, roleId, userPrivileges
#        return(0, "OK", accountid, storedRoleId, storedPrivileges )
#
#

##    # Post RolesCollection
#    # POST to roles collection  (add a custom role)
#    def postRolesResource(self, request, postData):
#        # generate headers for 4xx error messages
#        errhdrs = self.hdrs.rfRespHeaders(request )
#
#        # first verify that the client didn't send us a property we cant patch
#        # we need to fail the request if we cant handle any properties sent
#        #   note that this implementation does not support OemPrivileges
#        for key in postData:
#            if( (key != "Id") and (key != "AssignedPrivileges") and (key != "RoleId")):
#                return (4, 400, "Bad Request-Invalid Post Property Sent", "", errhdrs)
#        # now check that all required on create properties were sent as post data
#        privileges=None
#
#        # Note RedDrum allows sending either "Id" or "RoleId" because early schema definitions did not
#        #   include the RoldId property and clients like Redfishtool used Id to identify the role
#        #   Starting with Role.v1_2_0, the RoleId was added as RequiredOnCreate 
#        #   so RedDrum will require EITHER RoleId or Id and will use RoleId if both are sent
#        if( "RoleId" in postData):
#            roleId=postData['RoleId']
#        elif( "Id" in postData):
#            roleId=postData['Id']
#        else:
#            roleId=None
#
#        if("AssignedPrivileges" in postData):
#            privileges=postData['AssignedPrivileges']
#
#        if( (roleId is None) or (privileges is None) ):
#            return (4, 400, "Bad Request-Required On Create properties not all sent", "",errhdrs)
#
#        # now verify that the post data properties have valid values
#        if roleId in self.rolesDb:   # if the roleId already exists, return error
#            return (4, 400, "Bad Request-Invalid RoleId--RoleId already exists", "",errhdrs)
#        validPrivilegesList=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
#        for priv in privileges:
#            if priv not in validPrivilegesList:
#                return (4, 400, "Bad Request-Invalid Privilige", "",errhdrs)
#
#        # create response header data
#        locationUri="/redfish/v1/AccountService/Roles/" + roleId
#        #respHeaderData={"Location": locationUri}
#
#        # create rolesDb data and response properties
#        roleName=roleId + "Custom Role"
#        roleDescription="Custom Role"
#        isPredefined=False
#
#        # add the new role entry to add to the roleDb
#        self.rolesDb[roleId]={"RoleId": roleId, "Name": roleName, "Description": roleDescription, "IsPredefined": isPredefined, 
#            "AssignedPrivileges": privileges }
#
#        # write the data back out to the eventService/Roles database file
#        rolesDbJson=json.dumps(self.rolesDb,indent=4)
#        with open( self.rolesDbFilePath, 'w', encoding='utf-8') as f:
#            f.write(rolesDbJson)
#
#        # get the response data
#        rc,status,msg,respData,respHdr=self.getRoleEntry(request, roleId)
#        if( rc != 0):
#            #something went wrong--return 500
#            return(5, 500, "Error Getting New Role Data","",{})
#
#        # get the response Header with Link and Location headers
#        respHeaderData = self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri, resource=self.EventDestinationTemplate)
#
#        #return to flask uri handler, include location header
#        return(0, 201, "Created",respData,respHeaderData)
#
#
#
#    # delete the Role
#    # all we have to do is verify the roleid is correct--
#    # and then, if it is valid, delete the entry for that roleid from the rolesDb
#    # For reference: the rolesDb:
#    #    self.rolesDb[roleId]={"Name": rolename, "Description": roleDescription, "IsPredefined": idPredefined, 
#    #       "AssignedPrivileges": privileges }
#    def deleteRole(self, request, roleid):
#        # generate the headers
#        hdrs=self.hdrs.rfRespHeaders(request)
#
#        # First, verify that the roleid is valid
#        if roleid not in self.rolesDb:
#            return(4, 404, "Not Found","",hdrs)
#
#        # 2nd: verify this is not a pre-defined role that cannot be deleted
#        if self.rolesDb[roleid]["IsPredefined"] is True:
#            resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="Get" )
#            return(4, 405, "Method Not Allowed--Builtin Roles cannot be deleted","",resp405Hdrs)
#
#        # get the roleId name if it is included in the rolesDb
#        if "RoleId" in self.rolesDb[roleid]:
#            roleidName=self.rolesDb[roleid]["RoleId"]
#        else:
#            roleidName=roleid
#        
#        roleIdIsUsed=False
#        for accountid in self.eventDestinationCollectionDb:
#            if self.eventDestinationCollectionDb[accountid]["RoleId"]==roleidName:
#                roleIdIsUsed=True
#        if roleIdIsUsed is True:
#            return(4, 409, "Conflict-Role is being used by an existing user account", "", hdrs)
#
#        # otherwise go ahead and delete the roleid
#        del self.rolesDb[roleid]
#
#        return(0, 204, "No Content", "", hdrs)
#
#
#    # Patch Role
#    # PATCH a ROLE ENTRY
#    def patchRoleEntry(self, request, roleid, patchData):
#        # generate headers
#        hdrs = self.hdrs.rfRespHeaders(request)
#
#        # First, verify that the roleId is valid, 
#        if roleid not in self.rolesDb:
#            return(4, 404, "Not Found","",hdrs)
#
#        # verify this is not a pre-defined role that cannot be patched/modified
#        if self.rolesDb[roleid]["IsPredefined"] is True:
#            resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="Get" )
#            return(4, 405, "Method Not Allowed--Builtin Roles cannot be Patched","",resp405Hdrs)
#
#        # verify that the patch data is good
#        # first verify that ALL of the properties sent in patch data are patchable for redfish spec
#        for prop in patchData:
#            if prop != "AssignedPrivileges":
#                return (4, 400, "Bad Request-one or more properties not patchable", "",hdrs)
#
#        # check if any privilege is not valid
#        redfishPrivileges=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
#        if "AssignedPrivileges" in patchData:
#            for privilege in patchData["AssignedPrivileges"]:
#                if not privilege in redfishPrivileges:
#                    return (4, 400, "Bad Request-one or more Privileges are invalid", "",hdrs)
#
#        # if here, all values are good. Update the eventServiceDb dict
#        self.rolesDb[roleid]["AssignedPrivileges"]=patchData["AssignedPrivileges"]
#
#        #xg5 note: service currently does not support oem privileges
#
#        # write the rolesDb back out to the file
#        dbDictJson=json.dumps(self.rolesDb, indent=4)
#        with open( self.rolesDbFilePath, 'w', encoding='utf-8') as f:
#            f.write(dbDictJson)
#
#        return(0, 204, "No Content", "", hdrs)
#

## end
## NOTES TODO
## if you delete a role, verify that no user is assigned that role
## search for other TODOs
