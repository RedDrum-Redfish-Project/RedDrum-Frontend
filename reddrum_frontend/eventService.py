
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
    #statusChange = "StatusChange"
    #resourceUpdated = "ResourceUpdated"
    resourceAdded = "ResourceAdded"
    resourceRemoved= "ResourceRemoved"
    alert = "Alert"

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)
    

class RfEventService():  
    # Note that this resource was created in serviceRoot for the Account service.
    def __init__(self,rdr ):
        #TODO kill rdr references
        self.rdr=rdr
        self.loadResourceTemplates(rdr )
        self.loadEventServiceDatabaseFiles(rdr )
#       self.initializeSubscriptionsDict(rdr)
        self.hdrs=RfAddHeaders(rdr)

    def loadResourceTemplates( self, rdr ):
        #load EventService Template
        self.eventServiceTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventService.json")

        #load Events Collection Template
        self.subscriptionsTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventDestinationCollection.json")

        #load Events Entry Template
        self.subscriptionTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "EventDestination.json")

        #load Event Template
        self.eventTemplate=self.loadResourceTemplateFile(rdr.baseDataPath,"templates", "Event.json")

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

        # load the Events collection database file: "EventDestinationCollectionDb.json"
        filename="EventDestinationCollectionDb.json"
        self.subscriptionsDbFilePath,self.subscriptionsDb=self.loadDatabaseFile(rdr,"db",filename) 

        # load the Events collection database file: "EventsDb.json"
        #filename="EventsDb.json"
        #self.eventsDbFilePath,self.eventsDb=self.loadDatabaseFile(rdr,"db",filename) 

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

    # clear the EventService related database files
    def clearEventServiceDatabaseFiles(self, rdr ):
        filename="EventServiceDb.json"
        self.eventServiceDb=self.clearDatabaseFile(rdr,"db",filename) 

        filename="EventDestinationCollectionDb.json"
        self.subscriptionsDb=self.clearDatabaseFile(rdr,"db",filename) 

    def clearDatabaseFile( self, rdr, subDir, filename ):
        clearedDb=dict()
        dbFilePath=os.path.join(rdr.varDataPath,subDir, filename)

        if os.path.exists(dbFilePath):
            os.remove(dbFilePath)
        # return path and data
        return(clearedDb)

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
        # TODO where are allow methods defined in spec?
        allowMethods=["HEAD","GET"],
        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.eventServiceTemplate, allow=allowMethods)

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

        # Event Types; Currently only "Alert" is supported for now
        # TODO write custom JSON Encoder but use string for now
        resData2["EventTypesForSubscription"]  = ["Alert"]
            
        # Subscriptions
        resData2["Subscriptions"] = { "@odata.id": "/redfish/v1/EventService/Subscriptions" }

        # Action (SubmitTestEvent)
        #TODO properly implement Actions; Where should they be defined?
        resData2["Actions"] = self.eventServiceDb["Actions"] #e.g. "60"
        # create the response json data and return
        resp=json.dumps(resData2,indent=4)
        return(0, 200, "", resp, hdrs)

    #TODO do we need a separate EventSubscriptions class?
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
            hdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "",hdrs)

        #TODO is this correct headers?
        allowMethods=["HEAD","GET","PATCH","DELETE"], #is DELETE/PATCH allowed?
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
                                     resource=self.subscriptionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # copy the template subscriptionEntry resource
        resData2=dict(self.subscriptionTemplate)

        # now overwrite the dynamic data from the subscriptionsDb 
        subscriptionEntryUri="/redfish/v1/EventService/Subscriptions/" + subscriptionId
        resData2["@odata.id"]=subscriptionEntryUri
        resData2["Id"]=subscriptionId
        #TODO what is Name #resData2["Name"]=self.subscriptionsDb[subscriptionId]["Name"]
        resData2["Protocol"]=self.subscriptionsDb[subscriptionId]["Protocol"]
        resData2["Context"]=self.subscriptionsDb[subscriptionId]["Context"]
        resData2["Destination"]=self.subscriptionsDb[subscriptionId]["Destination"]
        #subscriptionType assumed to be "RedFishEvent"
        resData2["EventTypes"]=self.subscriptionsDb[subscriptionId]["EventTypes"]

        # convert to json
        jsonResponseData=(json.dumps(resData2,indent=4))

        return(0, 200, "", jsonResponseData, respHdrs)


    # PATCH EventService
    def patchEventServiceResource(self,request, patchData):
        # TODO privileges check?
        # TODO Do we allow GET and HEAD? 
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","PATCH"],
                                     resource=self.subscriptionsTemplate)
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # First check only patchable properties are present
        # Empty for now...so we don't support EventService patch at the moment
        # patchables=("DeliveryRetryAttempts","DeliveryRetryIntervalSeconds")
        # Or return annotated object response saying these are read-only properties...for now reject
        patchables=()

        if patchData is not None:
            return (4, 400, "Bad Request-Invalid Patch Property Received", "",errhdrs)
            
        for prop in patchData:
            if not prop in patchables:
                return (4, 400, "Bad Request-Invalid Patch Property Received", "",errhdrs)

        if( (patchData['DeliveryRetryAttempts'] is None) or (patchData['DeliveryRetryIntervalSeconds'] is None)):
            return (4, 400, "Bad Request-No patchable properties received", "",errhdrs)


        ##########################################
        # now verify that the Post data is valid #
        ##########################################

        for key in patchData:
            newVal=patchData[key]
            try:
                numVal=round(newVal)
            except ValueError:
                return(4,400,"invalid value","",hdrs)
            else:
                patchData[key]=numVal

        # then verify the properties passed-in are in valid ranges
        dlvyRtryAttempts=self.eventServiceDb['DeliveryRetryAttempts']
        dlvyRtryIntvlSecs=self.eventServiceDb['DeliveryRetryIntervalSeconds']

        if("DeliveryRetryAttempts" in patchData):
            dlvyRtryAttempts=patchData['DeliveryRetryAttempts']
        if("DeliveryRetryIntervalSeconds" in patchData):
            dlvyRtryIntvlSecs=patchData['DeliveryRetryIntervalSeconds']

        if( not (0 <= dlvyRtryAttempts < 5) or not(0 <= dlvyRtryIntvlSecs < 60) ):
            return(4,400,"Bad Request-Invalid value","",hdrs)

        # if here, all values are good. Update the eventServiceDb dict
        for key in patchData:
            self.eventServiceDb[key]=patchData[key]

        # write the data back out to the eventService database file
        eventServiceDbJson=json.dumps(self.eventServiceDb,indent=4)
        with open( self.eventServiceDbFilePath, 'w', encoding='utf-8') as f:
            f.write(eventServiceDbJson)
        return(0, 204, "", "", hdrs)


    # POST to Subscription collection  (add subscription)
    def postSubscriptionResource(self,request, postData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        postables=("Context","Destination","EventTypes", "Protocol")

        if not all (key in postData for key in postables):
            return (4, 400, "Bad Request-Invalid Post Property Sent", "", errhdrs)

        # Check all required on create properties were sent as post data
        if( (postData['Context'] is None) or (postData['Destination'] is None) or (postData['EventTypes'] is None) or (postData['Protocol'] is None ) ):
            return (4, 400, "Bad Request-Required On Create properties not all sent", "",errhdrs)

        context=None
        protocol=None
        eventDestination=None
        eventTypes=[""]

        if("Context" in postData):
            context=postData['Context']

        if("Protocol" in postData):
            protocol=postData['Protocol']

        if("Destination" in postData):
            eventDestination=postData['Destination']

        if("EventTypes" in postData):
            eventTypes=postData['EventTypes']



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
        if not isinstance(eventTypes, list):
            return (4, 400, "Bad Request-Context must be a list", "",errhdrs)
        for event in eventTypes:
            if not EventType.has_value(event):
                return (4, 400, "Bad Request-Supported EventType not sent", "",errhdrs)

        if not isinstance(context, str):
            return (4, 400, "Bad Request-Context must be a string", "",errhdrs)

        # create response header data
        subscriptionId=rfGenerateId(leading="E",size=8)
        locationUri="/redfish/v1/EventService/Subscriptions/" + subscriptionId

        # TODO add correct data ; add the new subscription entry to the eventDestinationCollectionDb
        postables=("Context","Destination","EventTypes", "Protocol")
        self.subscriptionsDb[subscriptionId]={"Context": context, "Destination": eventDestination, 
                   "Protocol": protocol, "EventTypes": eventTypes}

        #TODO 
        # write the EventDb back out to the file
        subscriptionsDbJson=json.dumps(self.subscriptionsDb, indent=4)
        with open( self.subscriptionsDbFilePath, 'w', encoding='utf-8') as f:
            f.write(subscriptionsDbJson)
        
        # get the response data
        rc,status,msg,respData,respHdr=self.getSubscriptionEntry(request, subscriptionId)
        if( rc != 0):
            #something went wrong--return 500
            return(5, 500, "Error Getting New Event Data","",{})

        # get the response Header with Link, and Location
        respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri,
                                     resource=self.subscriptionTemplate)

        #return to flask uri handler
        return(0, 201, "Created",respData,respHeaderData)

    # PATCH Subscription
    def patchSubscriptionEntry(self, request, subscriptionId, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # First, verify that the subscriptionIdId is valid, 
        if subscriptionId not in self.subscriptionsDb:
            return(4, 404, "Not Found","",hdrs)

        #first verify client didn't send us a property we cant patch
        # TODO complete list of patchables
        patchables=("Context")

        for key in patchData:
            if( not key in patchables ):
                return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)

        context=patchData["Context"]
        if not isinstance(context, str):
            return (4, 400, "Bad Request-Context must be a string", "",hdrs)

        self.subscriptionsDb[subscriptionId]["Context"]=context

        # write the EventDb back out to the file
        subscriptionsDbJson=json.dumps(self.subscriptionsDb, indent=4)
        with open( self.subscriptionsDbFilePath, 'w', encoding='utf-8') as f:
            f.write(subscriptionsDbJson)

        #return to flask uri handler
        return(0, 204, "No Content", "", hdrs)

    # Test Event Subscription
    # TODO not complete
    def sendTestEvent(self, request, postData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)
        #postables=("EventType","EventId", "EventTimestamp", "Severity", "Message", "MessageId", "MessageArgs", "OriginOfCondition")
        postables=("EventType","EventId","EventId","EventTimestamp","Severity","Message","MessageId","MessageArgs","OriginOfCondition")

        if not all (key in postData for key in postables):
            return (4, 400, "Bad Request-Invalid Object Post Property Sent", "", hdrs)

        if("EventType" in postData):
            eventType=postData['EventType']

        if("EventId" in postData):
            eventId=postData['EventId']

        if("EventTimestamp" in postData):
            eventTimestamp=postData['EventTimestamp']

        if("Severity" in postData):
            severity=postData['Severity']

        if("Message" in postData):
            message=postData['Message']

        if("MessageId" in postData):
            messageId=postData['MessageId']

        if("MessageArgs" in postData):
            messageArgs=postData['MessageArgs']

        if("OriginOfCondition" in postData):
            originOfCondition=postData['OriginOfCondition']

        stringProperties=("Severity", "Message", "MessageId", "MessageArgs", "OriginOfCondition")
        for key in stringProperties:
            if not isinstance(key, str):
                return (4, 400, "Bad Request-Property must be a string", "",hdrs)

        if not isinstance(eventTypes, list):
            return (4, 400, "Bad Request-Context must be a list", "",hdrs)

        for event in eventTypes:
            if not EventType.has_value(event):
                return (4, 400, "Bad Request-Supported EventType not sent", "",errhdrs)


        resData2=dict(self.eventTemplate)

        # add required properties
        # TODO Name Property?
        resData2["EventType"]  = eventType 
        resData2["EventId"]  = eventId
        resData2["EventTimeStamp"]  = eventTimestamp 
        resData2["Severity"]  = severity
        resData2["Message"]  = message
        resData2["MessageId"]  = messageId
        resData2["MessageArgs"]  = messageArgs
        resData2["OriginOfCondition"]  = originOfCondition

        # now overwrite the dynamic data from the subscriptionsDb 
        # create response header data
        # TODO
        #eventId=len(self.eventsDb) + 1
        #self.eventsDb[eventId]=postData
        #locationUri="/redfish/v1/EventService/Event/" + str(eventId)

        respHeaderData={}

        #TODO fire off event using redfish library or http library
        return(0, 201, "Created","",respHeaderData)
   
       
# DELETE Subscription
#    # delete the Subscription
#    # all we have to do is verify the subscriptionid is correct--
#    # and then, if it is valid, delete the entry for that subscriptionid from the eventDestinationCollectionDb and subscriptionsDict
    def deleteSubscriptionEntry(self, request, subscriptionid):
        hdrs=self.hdrs.rfRespHeaders(request)
        # generate the headers

        # First, verify that the subscriptionid is valid, 
        if subscriptionid not in self.subscriptionsDb:
            return(4, 404, "Not Found","",hdrs)

        # write the data back out to the eventService database file
        del self.subscriptionsDb[subscriptionid]
        eventDestinationCollectionDbJson=json.dumps(self.subscriptionsDb,indent=4)
        filename="SubscriptionsDb.json"
        with open( self.subscriptionsDbFilePath, 'w', encoding='utf-8') as f:
            f.write(eventDestinationCollectionDbJson)

        return(0, 204, "No Content","",hdrs)
## end
## NOTES TODO
## search for other TODOs
