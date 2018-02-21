
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
from .resource import RfStaticResource
from .generateId import rfGenerateId
#from .rootData import RfRoot
import json
import time
import sys
from  .redfish_headers import RfAddHeaders

class RfSessionService():  
    # Note that resource was created in serviceRoot for the session service.
    def __init__(self, rfr):
        self.rfr=rfr  #xg999fix
        self.rdr=rfr
        self.loadResourceTemplates(rfr )
        self.loadSessionServiceDatabase(rfr )
        self.initializeSessionsDict(rfr )
        self.hdrs=RfAddHeaders(rfr)
        self.magic="123456"

    def loadResourceTemplates( self, rfr ):
        #load SessionService Template
        indxFilePath=os.path.join(rfr.baseDataPath,"templates", "SessionService.json")
        if os.path.isfile(indxFilePath):
            self.sessionServiceTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rfr.logMsg("CRITICAL","*****ERROR: SessionService: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)

        #load Sessions Collection Template
        indxFilePath=os.path.join(rfr.baseDataPath,"templates", "SessionCollection.json")
        if os.path.isfile(indxFilePath):
            self.sessionsCollectionTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rfr.logMsg("CRITICAL","*****ERROR: SessionService: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)

        #load Session Entry Template
        indxFilePath=os.path.join(rfr.baseDataPath,"templates", "Session.json")
        if os.path.isfile(indxFilePath):
            self.sessionEntryTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rfr.logMsg("CRITICAL","*****ERROR: SessionService: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)
        
    def loadSessionServiceDatabase(self,rfr ):
        sessionServiceDbFilename="SessionServiceDb.json"
        self.sessionServiceDbFilePath=os.path.join(rfr.varDataPath,"db", sessionServiceDbFilename )
        if os.path.isfile(self.sessionServiceDbFilePath):
            self.sessionServiceDb=json.loads( open(self.sessionServiceDbFilePath,"r").read() )
        else:
            self.rfr.logMsg("WARNING",
               "*****WARNING: Json Data file:{} Does not exist. Creating default.".format(self.sessionServiceDbFilePath))
            # read the data in from the default database dir with the rm-tools package
            dfltDbFilePath=os.path.join(rfr.baseDataPath,"db", sessionServiceDbFilename)
            if os.path.isfile(dfltDbFilePath):
                self.sessionServiceDb=json.loads( open(dfltDbFilePath,"r").read() )
            else:
                self.rfr.logMsg("CRITICAL","*****ERROR: Default Json Database file:{} Does not exist. Exiting.".format(dfltDbFilePath))
                sys.exit(10)
            #write the data back out to the var directory where the dynamic db info is kept
            sessionServiceDbJson=json.dumps(self.sessionServiceDb,indent=4)
            with open( self.sessionServiceDbFilePath, 'w', encoding='utf-8') as f:
                f.write(sessionServiceDbJson)

    def initializeSessionsDict(self,rfr):
        # this is the in-memory database of open sessions
        # the sessionsDict is an dict indexed by   sessionsDict[sessionId][<sessionParameters>]
        #   self.sessionsDict[sessionid]=
        #       { "UserName": username,      "UserPrivileges": userPrivileges, "AccountId": accountid,
        #         "X-Auth-Token": authtoken, "LocationUri": locationUri,     "LastAccessTime": lastAccessTime }
        self.sessionsDict=dict() #create an empty dict of session entries
            
    # GET SessionService
    def getSessionServiceResource(self,request):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.sessionServiceTemplate, allow="GetPatch")

        # Process HEAD method
        if request.method=="HEAD":
            return(0,200,"","",hdrs)
        
        # create a copy of the SessionService resource template 
        resData2=dict(self.sessionServiceTemplate)

        # assign the required properties
        resData2["@odata.id"] = "/redfish/v1/SessionService"
        resData2["Id"] = "SessionService"
        resData2["Name"]= "RackManager Session Service"
        resData2["Description"] = "RackManager Session Service"

        # assign link to the Sessions collection
        resData2["Sessions"] = {"@odata.id": "/redfish/v1/SessionService/Sessions"}

        # set the dynamic data in the template copy to the value in the sessionService database
        resData2["SessionTimeout"]=self.sessionServiceDb["SessionTimeout"]

        # create the response json data and return
        resp=json.dumps(resData2,indent=4)

        # generate the headers and return the response
        return(0,200,"",resp,hdrs)

    # PATCH SessionService
    def patchSessionServiceResource(self, request, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        #first verify client didn't send us a property we cant patch
        for key in patchData:
            if( key != "SessionTimeout" ):
                return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)
        # now patch the valid properties sent
        if( "SessionTimeout" in patchData):
            newVal=patchData['SessionTimeout']
            if( (newVal < 30) or (newVal >86400) ):
                return(4, 400, "Bad Request-not in correct range", "", hdrs)
            else:
                # the data is good and in range, save it and return ok
                self.sessionServiceDb["SessionTimeout"]=newVal

                # write the data back out to the sessionService database file
                sessionServiceDbJson=json.dumps(self.sessionServiceDb,indent=4)
                with open( self.sessionServiceDbFilePath, 'w', encoding='utf-8') as f:
                    f.write(sessionServiceDbJson)

                # return to URI handling OK, with no content
                return(0, 204, "", "", hdrs)
        else:
            return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)


    # getSessionAuthInfo()
    #   returns: rc, errMsgString, sessionId, authToken, userPrivileges, accountId, username
    #      rc=404 if sessionId is invalid.  
    #      rc=401 if authToken is invalid or mismatches sessionid, or session is expired
    #   self.sessionsDict[sessionid]={"UserName": username, "UserPrivileges": userPrivileges, 
    #       "AccountId": accountid,
    #       "X-Auth-Token": authtoken, "LocationUri": locationUri, "LastAccessTime": lastAccessTime}
    def getSessionAuthInfo(self,sessionid=None, authtoken=None ):
        storedAuthToken=None
        storedSessionId=None
        storedPrivileges=None
        # if sessionid is not None, verify that the sessionId is valid
        if sessionid is not None:
            if sessionid not in self.sessionsDict:
                return(404, "SessionId Not Found",None,None,None,None,None)
            else:
                #the sessionid exists, so get associated authToken
                storedSessionId=sessionid
                storedAuthToken=self.sessionsDict[sessionid]["X-Auth-Token"]
                storedPrivileges=self.sessionsDict[sessionid]["UserPrivileges"]
                storedUserName=self.sessionsDict[sessid]["UserName"]
                storedAccountId=self.sessionsDict[sessid]["AccountId"]
                # if authtoken was also passed in, check if it matches the stored value
                if authtoken is not None:
                    if(authtoken != storedAuthToken):
                        return(401, "Not Authroized-AuthToken Incorrect",None,None,None,None,None)

        # else if authtoken is not None, look it up, verify it exists
        elif authtoken is not None:
            # case where sessionid was not passed in, but authtoken was
            # we need to go lookup authtoken w/o sessionid
            foundToken=False
            for sessid in self.sessionsDict:
                if( self.sessionsDict[sessid]["X-Auth-Token"] == authtoken ):
                    foundToken=True
                    storedSessionId=sessid
                    storedAuthToken=self.sessionsDict[sessid]["X-Auth-Token"]
                    storedPrivileges=self.sessionsDict[sessid]["UserPrivileges"]
                    storedUserName=self.sessionsDict[sessid]["UserName"]
                    storedAccountId=self.sessionsDict[sessid]["AccountId"]
                    break
            if foundToken is False:
                return(401, "Not Authroized-Token Not Found",None,None,None,None,None)

        # else, both sessionid and authtoken are None, which is invalid call
        else:
            return(500, "Invalid Auth Check",None,None,None,None,None)

        # verify that the session has not expired
        currentTime=int(time.time())
        lastAccessTime=self.sessionsDict[storedSessionId]["LastAccessTime"]
        sessionTimeout=self.sessionServiceDb["SessionTimeout"] 
        if( (currentTime - lastAccessTime) > sessionTimeout ):
            # it timed out.  delete the session, and return unauthorized
            del self.sessionsDict[storedSessionId]
            # return 404 since we deleted the session and the uri is no longer valid
            return(404, "Session Not Found-Expired",None,None,None,None,None)
        else:
            #else-update the timestamp--to indicate the session was used
            self.sessionsDict[storedSessionId]["LastAccessTime"]=currentTime

        # if here, all ok, return privileges
        #returns: rc, errMsgString, sessionId, authToken, userPrivileges
        return(0, "OK", storedSessionId, storedAuthToken, storedPrivileges, storedAccountId, storedUserName )


    # ------------Session Collection Functions----------------

    # Post Sessions
    # POST to sessions collection  (Login)
    def postSessionsResource(self,request, postData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # process special cases for request coming in over http or https based on RedDrum.conf auth config settings
        #requestHeadersLower = {k.lower() : v.lower() for k,v in request.headers.items()}
        #print("EEEEEEEE: hdrs: {}".format(requestHeadersLower))
        #if "X-Rm-From-Rproxy" in requestHeadersLower and requestHeadersLower["x-rm-from-rproxy"]=="https":
        if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTPS":
            # case: scheme is https,  so execute the API
            pass
        elif self.rdr.RedfishAllowSessionLoginOverHttp is True:
            # case: scheme=http,  but login over http is allowed, so execute the API
            pass
        else:
            # case: scheme=http, login over http is NOT allowed
            #  so return a 404-Not Found  status
            return(4, 404, "404-Not Found-URI not supported over http", "", errhdrs)


        # verify that the client didn't send us a property we cant initialize the session with
        # we need to fail the request if we cant handle any properties sent
        for key in postData:
            if( (key != "UserName") and (key != "Password") ):
                return (4, 400, "Bad Request-Invalid Post Property Sent", "", errhdrs)

        # now check that all required on create properties were sent as post data
        username=None
        password=None
        if( "UserName" in postData):
            username=postData['UserName']

        if("Password" in postData):
            password=postData['Password']

        if( (username is None) or (password is None) ):
            return (4, 400, "Bad Request-Required On Create properties not all sent", "", errhdrs)

        # now verify that the login credentials are valid and get the privileges
        rc,errMsg,accountid,roleId,userPrivileges=self.rfr.root.accountService.getAccountAuthInfo(username,password)
        if( rc != 0 ): # unauthenticated
            return(4, 401, "Unauthorized--invalid user or password","", errhdrs)

        # otherwise, if here, it is an authenticated user
        # check if user has login privilege
        if( "Login" not in userPrivileges ):
            return(4, 401, "Unauthorized--User does not have login privilege","", errhdrs)

        #get time to update timer in sessDict
        lastAccessTime=int(time.time())

        # now Generate a session ID and auth token as a random number
        sessionid=rfGenerateId(leading="S",size=8)
        authtoken=rfGenerateId(leading="A",size=8)

        # Generate the location header
        locationUri="/redfish/v1/SessionService/Sessions/" + sessionid

        # add the new session entry to add to the sessionsDict
        self.sessionsDict[sessionid]={"UserName": username, "UserPrivileges": userPrivileges, "AccountId": accountid,
                  "X-Auth-Token": authtoken, "LocationUri": locationUri, "LastAccessTime": lastAccessTime}

        # get the response data
        rc,status,msg,respData,respHdr=self.getSessionEntry(request, sessionid)
        if( rc != 0):
            #something went wrong--return 500
            return(5, 500, "Error Getting New Session Data","",{})

        # get the response Header with Link, Location, and X-Auth-Token headers
        respHeaderData = self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri, xauthtoken=authtoken, 
                                                 resource=self.sessionEntryTemplate)
        #return to flask uri handler
        return(0, 201, "Created", respData, respHeaderData)



    # GET SessionsCollection
    # GET sessions Collection
    def getSessionsCollectionResource(self, request ):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"], 
                                     resource=self.sessionsCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # the routine copies a template file with the static redfish parameters
        # then it updates the dynamic properties from the sessionsDict
        # for SessionCollection GET, build the Members array

        # first walk the sessionsDict and check if any sessions have timed-out.
        # If any session has timed-out, delete it now
        currentTime=int(time.time())
        sessionTimeout=self.sessionServiceDb["SessionTimeout"]
        sessDict2=dict(self.sessionsDict)
        for sessionid in sessDict2.keys():
            # check if this session entry has timed-out.   If so, delete it.
            lastAccessTime=sessDict2[sessionid]["LastAccessTime"]
            if( (currentTime - lastAccessTime) > sessionTimeout ):
                # this session is timed out.  remove it from the original sessionDict
                del self.sessionsDict[sessionid]

        # Then copy the sessionsCollection template file (which has an empty sessions array)
        resData2=dict(self.sessionsCollectionTemplate)
        count=0
        # now walk through the entries in the sessionsDict and built the sessionsCollection Members array
        # not that it starts out an empty array
        for sessionEntry in self.sessionsDict.keys():
            # increment members count, and create the member for the next entry
            count=count+1
            newMember=[{"@odata.id": self.sessionsDict[sessionEntry]["LocationUri"] } ]

            # add the new member to the members array we are building
            resData2["Members"] = resData2["Members"] + newMember
        resData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=json.dumps(resData2,indent=4)

        return(0, 200, "",jsonRespData2, hdrs)

    # GET Session Entry
    def getSessionEntry(self,request, sessionid):
        # generate error header for 4xx errors
        errhdrs=self.hdrs.rfRespHeaders(request)

        # First: verify that the sessionId is valid
        if sessionid not in self.sessionsDict:
            return(4, 404, "Not Found", "",errhdrs)

        # Second: Check if the session has timed-out.
        # If it has timed-out, delete it now, and re-check if session is not found
        currentTime=int(time.time())
        sessionTimeout=self.sessionServiceDb["SessionTimeout"]
        lastAccessTime=self.sessionsDict[sessionid]["LastAccessTime"]
        if( (currentTime - lastAccessTime) > sessionTimeout ):
            # this session is timed out.  remove it from the sessionDict
            del self.sessionsDict[sessionid]

        # re-verify if the session exists - since we may have just removed it
        if sessionid not in self.sessionsDict:
            return(4, 404, "Not Found", "",errhdrs)

        # generate header info
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","DELETE"], 
                                     resource=self.sessionEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # copy the template sessionEntry resource
        resData=dict(self.sessionEntryTemplate)

        # construct response properties
        resData["Name"]="Session Resource"
        resData["Description"]="Resource for a specific session that was created"
        resData["Id"]=sessionid
        resData["UserName"]=self.sessionsDict[sessionid]["UserName"]
        resData["@odata.id"]=self.sessionsDict[sessionid]["LocationUri"]

        # convert to json
        jsonRespData=(json.dumps(resData,indent=4))

        return(0, 200, "", jsonRespData, respHdrs)

    # Delete Session,  logout,  delete the session
    #   all we have to do is verify the sessionid is correct--
    #   and then, if it is valid, delete the entry for that sessionid from the sessionsDict
    #   For reference:  self.sessionsDict[sessionid]=
    #       { "UserName": username,      "UserPrivileges": userPrivileges, "AccountId": accountid,
    #         "X-Auth-Token": authtoken, "LocationUri": locationUri,     "LastAccessTime": lastAccessTime }
    def deleteSession(self, request, sessionid):
        # generate the headers
        hdrs=self.hdrs.rfRespHeaders(request)

        # First, verify that the sessionid is valid
        if sessionid not in self.sessionsDict:
            return(4, 404, "Not Found","",hdrs)

        # verify authorization credentials
        # if we got here, we know the user authenticated and has privilege "ConfigureManager" or "Login"
        #   if user privileges include ConfigureManager, always execute the API
        #   if user privileges do not include ConfigureManager, but do include Login, 
        #        then ONLY execute the API if the session belongs to "This User"  
        isAuthorized=False
        if "ConfigureManager" in self.rdr.root.accountService.currentUserPrivileges:
            # this user has admin privileges for the sessions so it can delete any users session
            isAuthorized=True
        elif "Login" in self.rdr.root.accountService.currentUserPrivileges:
            # this user only has privileges to delete its own sessions.  
            # check if sessionid is owned by the authenticated user
            sessionAccountId = self.sessionsDict[sessionid]["AccountId"]
            if sessionAccountId == self.rdr.root.accountService.currentUserAccountId:
                # this user only has privileges to delete its own sessions
                isAuthorized=True

        # return 403 Unauthorized if authorization failed here
        if isAuthorized is False:
            return(4, 403, "Forbidden-Privileges not sufficient","",hdrs)
            
        # if here, authorization passesd.  delete the session and return 204   
        del self.sessionsDict[sessionid]

        return(0, 204, "No Content", "", hdrs)

# end
