
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
import hashlib
# support passlib v1.7.0 or later
#from passlib.hash import sha512_crypt
#from passlib.hash import plaintext
from passlib.context import CryptContext
from .redfish_headers import RfAddHeaders


class RfAccountService():  
    # Note that this resource was created in serviceRoot for the Account service.
    def __init__(self,rfr ):
        self.rfr=rfr
        self.rdr=rfr
        self.loadResourceTemplates(rfr )
        self.loadAccountServiceDatabaseFiles(rfr )
        self.initializeAccountsDict(rfr)
        self.cryptContext = CryptContext(schemes=["sha512_crypt","sha256_crypt", "plaintext"]) # supported passwd schemes in db
            # NOTE that plaintext must be last--since all other schemes could be plaintext
        self.cryptContext.update(default="sha512_crypt") # strictly assign sha512 as the scheme used when "Setting" passwds
        self.cryptContext.update(sha512_crypt__default_rounds=5000)  # sets normal linux rounds=5000, otherwise it is very slow

        # default currentUserId and currentUserPrivileges to None
        #   these are used by APIs that need to do auththen or authroization checking inside the API eg Patch account or Delete Session
        self.currentUserAccountId=None
        self.currentUserPrivileges=None

        self.hdrs=RfAddHeaders(rfr)
        self.magic="123456"

    def loadResourceTemplates( self, rfr ):
        #load AccountService Template
        self.accountServiceTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "AccountService.json")

        #load Accounts Collection Template
        self.accountsCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ManagerAccountCollection.json")

        #load Account Entry Template
        self.accountEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "ManagerAccount.json")

        #load Roles Collection Template
        self.rolesCollectionTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "RoleCollection.json")

        #load Roles Entry Template
        self.roleEntryTemplate=self.loadResourceTemplateFile(rfr.baseDataPath,"templates", "Role.json")

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
            self.rfr.logMsg("CRITICAL", 
               "*****ERROR: AccountService: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)
        
    def loadAccountServiceDatabaseFiles(self, rfr ):
        # load the AccountService database file:      "AccountServiceDb.json"
        filename="AccountServiceDb.json"
        self.accountServiceDbFilePath,self.accountServiceDb=self.loadDatabaseFile(rfr,"db",filename) 

        # load the Accounts collection database file: "AccountsDb.json"
        filename="AccountsDb.json"
        self.accountsDbFilePath,self.accountsDb=self.loadDatabaseFile(rfr,"db",filename) 

        # load the Roles collection  database file:     "RolesDb.json"
        filename="RolesDb.json"
        self.rolesDbFilePath,self.rolesDb=self.loadDatabaseFile(rfr,"db",filename) 

    # worker function called by loadAccountServiceDatabaseFiles() to load a specific database file
    # returns two positional parameters:
    #    the database filepath,
    #    a dict of the database file
    # if file does not exist in the varDataPath/subDir directory (the database dir), 
    #   then it loads the file from baseDataBath (the default database), and saves it back to the varDataPath dir
    # assumes good json in the database file
    def loadDatabaseFile( self, rfr, subDir, filename ):
        dbFilePath=os.path.join(rfr.varDataPath,subDir, filename)
        if os.path.isfile(dbFilePath):
            dbDict=json.loads( open(dbFilePath,"r").read() )
        else:
            self.rfr.logMsg("INFO","*****WARNING: Json Data file:{} Does not exist. Creating default.".format(dbFilePath))
            # read the data in from the default database dir with the rm-tools package
            dfltDbFilePath=os.path.join(rfr.baseDataPath,subDir,filename)
            if os.path.isfile(dfltDbFilePath):
                dbDict=json.loads( open(dfltDbFilePath,"r").read() )
            else:
                self.rfr.logMsg("CRITICAL", 
                    "*****ERROR: Default Json Database file:{} Does not exist. Exiting.".format(dfltDbFilePath))
                sys.exit(10)
            #write the data back out to the var directory where the dynamic db info is kept
            dbDictJson=json.dumps(dbDict,indent=4)
            with open( dbFilePath, 'w', encoding='utf-8') as f:
                f.write(dbDictJson)
        # return path and data
        return(dbFilePath,dbDict)

    def clearAccountServiceDatabaseFiles(self, rfr ):
        # clear the AccountService database file:      "AccountServiceDb.json"
        filename="AccountServiceDb.json"
        self.accountServiceDb=self.clearDatabaseFile(rfr,"db",filename) 

        # clear the Accounts collection database file: "AccountsDb.json"
        filename="AccountsDb.json"
        self.accountsDb=self.clearDatabaseFile(rfr,"db",filename) 

        # clear the Roles collection  database file:     "RolesDb.json"
        filename="RolesDb.json"
        self.rolesDb=self.clearDatabaseFile(rfr,"db",filename) 

    def clearDatabaseFile( self, rfr, subDir, filename ):
        clearedDb=dict()
        dbFilePath=os.path.join(rfr.varDataPath,subDir, filename)
        #write the data back out to the var directory where the dynamic db info is kept
        dbDictJson=json.dumps(clearedDb,indent=4)
        with open( dbFilePath, 'w', encoding='utf-8') as f:
                f.write(dbDictJson)
        # return path and data
        return(clearedDb)

    def initializeAccountsDict(self,rfr):
        # this is the in-memory database of account properties that are not persistent
        # the accountsDict is a dict indexed by   accountsDict[accountid][<nonPersistentAccountParameters>]
        #   self.accountsDict[accountid]=
        #       { "Locked": <locked>,  "FailedLoginCount": <failedLoginCnt>, "LockedTime": <lockedTimestamp>,
        #         "AuthFailTime": <authFailTimestamp> }
        self.accountsDict=dict() #create an empty dict of Account entries
        curTime=time.time()

        #create the initial state of the accountsDict from the accountsDb
        for acct in self.accountsDb:
            self.accountsDict[acct]={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }
        
            
    # GET AccountService
    def getAccountServiceResource(self,request):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.accountServiceTemplate, allow="GetPatch")

        # Process HEAD method
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # create a copy of the AccountService resource template 
        resData2=dict(self.accountServiceTemplate)

        # add required properties
        resData2["@odata.id"] = "/redfish/v1/AccountService"
        resData2["Id"] = "AccountService"
        resData2["Name"] = "Account Service"
        resData2["Description"] = "RackManager User Account Service"

        # add links to Accounts and Roles collections
        resData2["Accounts"] = { "@odata.id": "/redfish/v1/AccountService/Accounts" }
        resData2["Roles"] = { "@odata.id": "/redfish/v1/AccountService/Roles" }

        # set the dynamic data in the template copy to the value in the accountService database
        resData2["AuthFailureLoggingThreshold"]=self.accountServiceDb["AuthFailureLoggingThreshold"]
        resData2["MinPasswordLength"]=self.accountServiceDb["MinPasswordLength"]
        resData2["AccountLockoutThreshold"]=self.accountServiceDb["AccountLockoutThreshold"]
        resData2["AccountLockoutDuration"]=self.accountServiceDb["AccountLockoutDuration"]
        resData2["AccountLockoutCounterResetAfter"]=self.accountServiceDb["AccountLockoutCounterResetAfter"]
        if "MaxPasswordLength" in self.accountServiceDb:  # early RedDrum did not support MaxPasswordLength
            resData2["MaxPasswordLength"] = self.accountServiceDb["MaxPasswordLength"]
        if "ServiceEnabled" in self.accountServiceDb:  # early RedDrum did not support ServiceEnabled
            resData2["ServiceEnabled"]= self.accountServiceDb["ServiceEnabled"]

        # create the response json data and return
        resp=json.dumps(resData2,indent=4)
        return(0, 200, "", resp, hdrs)

    # PATCH AccountService
    def patchAccountServiceResource(self, request, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        #first verify client didn't send us a property we cant patch
        patachables=("AccountLockoutThreshold", "AuthFailureLoggingThreshold",
                     "AccountLockoutDuration","AccountLockoutCounterResetAfter")
        for key in patchData:
            if( not key in patachables ):
                return (4, 400, "Bad Request-Invalid Patch Property Sent", "", hdrs)

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
        newDuration=self.accountServiceDb["AccountLockoutDuration"]
        newResetAfter=self.accountServiceDb["AccountLockoutCounterResetAfter"]
        if( "AccountLockoutDuration" in patchData ):
            newDuration=patchData["AccountLockoutDuration"]
        if( "AccountLockoutCounterResetAfter" in patchData ):
            newResetAfter=patchData["AccountLockoutCounterResetAfter"]
        if( newDuration < newResetAfter ):
            return(4,400,"Bad Request-Invalid value","",hdrs)

        # if here, all values are good. Update the accountServiceDb dict
        for key in patchData:
            self.accountServiceDb[key]=patchData[key]

        # write the data back out to the accountService database file
        accountServiceDbJson=json.dumps(self.accountServiceDb,indent=4)
        with open( self.accountServiceDbFilePath, 'w', encoding='utf-8') as f:
            f.write(accountServiceDbJson)
        return(0, 204, "", "", hdrs)

    # getAccountAuthInfo(username,password)
    #   returns: rc, errMsgString, accountId, roleId, userPrivileges
    #      rc=404 if username is not in accountsDb
    #      rc=401 if username is invalid or mismatches password, or account is locked or not enabled
    #        =0   if authenticated
    #   self.accountsDict[accountid]={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }

    def getAccountAuthInfo(self, username, password ):
        authFailed=False
        storedUsername=None
        storedPassword=None
        storedPrivileges=None
        # if username or password is not None, it is an error
        if username is None:
            return(500, "Invalid Auth Check for username",None,None,None)
        if password is None:
            return(500, "Invalid Auth Check for password",None,None,None)

        # from username, lookup accountId --- they are not necessarily the same
        accountid=None
        for acctid in self.accountsDb:
            if( username == self.accountsDb[acctid]["UserName"] ):
                accountid=acctid
                break

        # if we didn't find the username, return error
        # since the username is invalid, we cant count invalid login attempts
        if accountid is None:
            return(404, "Not Found-Username Not Found",None,None,None)

        # check if the account is disabled
        if( self.accountsDb[accountid]["Enabled"] is False ): 
            return(401, "Not Authorized--Account Disabled",None,None,None)

        # check if account was locked 
        #    if it is locked but has now exceeded LockoutDuration then unlock and continue
        #    if it is locked and not exceeded lockout duration, return 401 Not authorized
        curTime=time.time()
        if self.accountsDict[accountid]["Locked"] is True:
            if( (curTime - self.accountsDict[accountid]["LockedTime"]) > self.accountServiceDb["AccountLockoutDuration"] ):
                # the lockout duration has expired.   unlock it.
                self.accountsDict[accountid]["Locked"]=False
                self.accountsDict[accountid]["LockedTime"]=0
                self.accountsDict[accountid]["FailedLoginCount"]=0
                self.accountsDict[accountid]["AuthFailTime"]=0
            else:
                # lockout duration has not expired, return auth error
                return(401, "Not Authorized--Account Locked By Service",None,None,None)

        #the accountid exists, and account is enabled and not locked

        #reset the AuthFailTime if time since last login failure is > AccountLockoutCounterResetAfter
        authFailTime=self.accountsDict[accountid]["AuthFailTime"]
        if( authFailTime != 0 ):
            # if we have had failures and are counting authentication failures
            resetAfterThreshold=self.accountServiceDb["AccountLockoutCounterResetAfter"]
            if( ( curTime - authFailTime ) > resetAfterThreshold ):
                # if time since last failure is greater than the reset counter threshold, then reset the counters
                self.accountsDict[accountid]["AuthFailTime"]=0
                self.accountsDict[accountid]["FailedLoginCount"]=0

        #now check the associated password to see if authentication passis this time 
        #check password
        #xg11
        #if( password != self.accountsDb[accountid]["Password"] ): # TODO change to check hash
        if self.cryptContext.verify(password, self.accountsDb[accountid]["Password"]) is not True:
            # authentication failed.

            # check if lockout on authentication failures is enabled
            lockoutThreshold=self.accountServiceDb["AccountLockoutThreshold"]
            lockoutDuration=self.accountServiceDb["AccountLockoutDuration"]

            # lockoutThreshold and lockoutDuration must BOTH be non-zero to enable lock on auth failures
            if( (lockoutThreshold > 0) and (lockoutDuration > 0) ):
                # check if we have now exceeded the login failures and need to lock the account
                failedLoginCount=self.accountsDict[accountid]["FailedLoginCount"] + 1
                if( failedLoginCount >= lockoutThreshold ):
                    # lock the account and clear the AuthFailTime and FailedLogin counters
                    self.accountsDict[accountid]["Locked"]=True
                    self.accountsDict[accountid]["LockedTime"]=curTime
                    self.accountsDict[accountid]["AuthFailTime"]=0
                    self.accountsDict[accountid]["FailedLoginCount"]=0
                    return(401, "Not Authorized--Password Incorrect and Account is now Locked By Service",None,None,None)
                else:
                    # we have not exceeded the failed authN threshold, update the counter and continue
                    self.accountsDict[accountid]["FailedLoginCount"]=failedLoginCount
                    self.accountsDict[accountid]["AuthFailTime"]=curTime
                    return(401, "Not Authorized--Password Incorrect",None,None,None)

            else:
                # case where account lockout is not enabled
                return(401, "Not Authorized--Password Incorrect",None,None,None)

        #if here, the authentication was successful
        #reset the lockout timers
        self.accountsDict[accountid]["FailedLoginCount"]=0
        self.accountsDict[accountid]["AuthFailTime"]=0

        storedpassword=self.accountsDb[accountid]["Password"]
        storedRoleId=self.accountsDb[accountid]["RoleId"]
        storedPrivileges=self.rolesDb[storedRoleId]["AssignedPrivileges"]

        # if here, all ok, return privileges
        #   returns:  rc, errMsgString, userName, roleId, userPrivileges
        return(0, "OK", accountid, storedRoleId, storedPrivileges )




    # ------------Roles Collection Functions----------------

    # GET RolesCollection
    # GET roles Collection
    def getRolesCollectionResource(self, request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"],
                                     resource=self.rolesCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # the routine copies a template file with the static redfish parameters
        # then it updates the dynamic properties from the rolesDb dict
        # for RolesCollection GET, we build the Members array

        # copy the rolesCollection template file (which has an empty roles array)
        resData2=dict(self.rolesCollectionTemplate)
        count=0
        # now walk through the entries in the rolesDb and build the rolesCollection Members array
        # note that the members array is an empty array in the template
        roleUriBase="/redfish/v1/AccountService/Roles/"
        for roleid in self.rolesDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=roleUriBase + roleid
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            resData2["Members"] = resData2["Members"] + newMember
        resData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(resData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)


    # GET Role Entry
    def getRoleEntry(self, request, roleid):

        # First verify that the roleId is valid
        if roleid not in self.rolesDb:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "",errhdrs)

        # generate header info depending on the specific roleId
        # predefined roles cannot be deleted or modified
        #     self.rolesDb[roleid]={"Name": rolename, "Description": roleDescription, "IsPredefined": idPredefined, 
        #                       "AssignedPrivileges": privileges }
        if self.rolesDb[roleid]["IsPredefined"] is True:
            # pre-defined roles cannot be deleted or modified
            allowMethods="Get"
        else:
            allowMethods=["HEAD","GET","PATCH","DELETE"],
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
                                     resource=self.roleEntryTemplate)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # copy the template roleEntry resource
        resData2=dict(self.roleEntryTemplate)

        # now overwrite the dynamic data from the rolesDb 
        roleEntryUri="/redfish/v1/AccountService/Roles/" + roleid
        resData2["@odata.id"]=roleEntryUri
        resData2["Id"]=roleid
        resData2["Name"]=self.rolesDb[roleid]["Name"]
        resData2["Description"]=self.rolesDb[roleid]["Description"]
        resData2["IsPredefined"]=self.rolesDb[roleid]["IsPredefined"]
        resData2["AssignedPrivileges"]=self.rolesDb[roleid]["AssignedPrivileges"]
        if "RoleId" in self.rolesDb[roleid]:
            resData2["RoleId"]=self.rolesDb[roleid]["RoleId"]
        else:
            resData2["RoleId"]=roleid

        # convert to json
        jsonResponseData=(json.dumps(resData2,indent=4))

        return(0, 200, "", jsonResponseData, respHdrs)


    # Post RolesCollection
    # POST to roles collection  (add a custom role)
    def postRolesResource(self, request, postData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # first verify that the client didn't send us a property we cant patch
        # we need to fail the request if we cant handle any properties sent
        #   note that this implementation does not support OemPrivileges
        for key in postData:
            if( (key != "Id") and (key != "AssignedPrivileges") and (key != "RoleId")):
                return (4, 400, "Bad Request-Invalid Post Property Sent", "", errhdrs)
        # now check that all required on create properties were sent as post data
        privileges=None

        # Note RedDrum allows sending either "Id" or "RoleId" because early schema definitions did not
        #   include the RoldId property and clients like Redfishtool used Id to identify the role
        #   Starting with Role.v1_2_0, the RoleId was added as RequiredOnCreate 
        #   so RedDrum will require EITHER RoleId or Id and will use RoleId if both are sent
        if( "RoleId" in postData):
            roleId=postData['RoleId']
        elif( "Id" in postData):
            roleId=postData['Id']
        else:
            roleId=None

        if("AssignedPrivileges" in postData):
            privileges=postData['AssignedPrivileges']

        if( (roleId is None) or (privileges is None) ):
            return (4, 400, "Bad Request-Required On Create properties not all sent", "",errhdrs)

        # now verify that the post data properties have valid values
        if roleId in self.rolesDb:   # if the roleId already exists, return error
            return (4, 400, "Bad Request-Invalid RoleId--RoleId already exists", "",errhdrs)
        validPrivilegesList=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
        for priv in privileges:
            if priv not in validPrivilegesList:
                return (4, 400, "Bad Request-Invalid Privilige", "",errhdrs)

        # create response header data
        locationUri="/redfish/v1/AccountService/Roles/" + roleId
        #respHeaderData={"Location": locationUri}

        # create rolesDb data and response properties
        roleName=roleId + "Custom Role"
        roleDescription="Custom Role"
        isPredefined=False

        # add the new role entry to add to the roleDb
        self.rolesDb[roleId]={"RoleId": roleId, "Name": roleName, "Description": roleDescription, "IsPredefined": isPredefined, 
            "AssignedPrivileges": privileges }

        # write the data back out to the accountService/Roles database file
        rolesDbJson=json.dumps(self.rolesDb,indent=4)
        with open( self.rolesDbFilePath, 'w', encoding='utf-8') as f:
            f.write(rolesDbJson)

        # get the response data
        rc,status,msg,respData,respHdr=self.getRoleEntry(request, roleId)
        if( rc != 0):
            #something went wrong--return 500
            return(5, 500, "Error Getting New Role Data","",{})

        # get the response Header with Link and Location headers
        respHeaderData = self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri, resource=self.roleEntryTemplate)

        #return to flask uri handler, include location header
        return(0, 201, "Created",respData,respHeaderData)



    # delete the Role
    # all we have to do is verify the roleid is correct--
    # and then, if it is valid, delete the entry for that roleid from the rolesDb
    # For reference: the rolesDb:
    #    self.rolesDb[roleId]={"Name": rolename, "Description": roleDescription, "IsPredefined": idPredefined, 
    #       "AssignedPrivileges": privileges }
    def deleteRole(self, request, roleid):
        # generate the headers
        hdrs=self.hdrs.rfRespHeaders(request)

        # First, verify that the roleid is valid
        if roleid not in self.rolesDb:
            return(4, 404, "Not Found","",hdrs)

        # 2nd: verify this is not a pre-defined role that cannot be deleted
        if self.rolesDb[roleid]["IsPredefined"] is True:
            resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="Get" )
            return(4, 405, "Method Not Allowed--Builtin Roles cannot be deleted","",resp405Hdrs)

        # get the roleId name if it is included in the rolesDb
        if "RoleId" in self.rolesDb[roleid]:
            roleidName=self.rolesDb[roleid]["RoleId"]
        else:
            roleidName=roleid
        
        roleIdIsUsed=False
        for accountid in self.accountsDb:
            if self.accountsDb[accountid]["RoleId"]==roleidName:
                roleIdIsUsed=True
        if roleIdIsUsed is True:
            return(4, 409, "Conflict-Role is being used by an existing user account", "", hdrs)

        # otherwise go ahead and delete the roleid
        del self.rolesDb[roleid]

        return(0, 204, "No Content", "", hdrs)


    # Patch Role
    # PATCH a ROLE ENTRY
    def patchRoleEntry(self, request, roleid, patchData):
        # generate headers
        hdrs = self.hdrs.rfRespHeaders(request)

        # First, verify that the roleId is valid, 
        if roleid not in self.rolesDb:
            return(4, 404, "Not Found","",hdrs)

        # verify this is not a pre-defined role that cannot be patched/modified
        if self.rolesDb[roleid]["IsPredefined"] is True:
            resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="Get" )
            return(4, 405, "Method Not Allowed--Builtin Roles cannot be Patched","",resp405Hdrs)

        # verify that the patch data is good
        # first verify that ALL of the properties sent in patch data are patchable for redfish spec
        for prop in patchData:
            if prop != "AssignedPrivileges":
                return (4, 400, "Bad Request-one or more properties not patchable", "",hdrs)

        # check if any privilege is not valid
        redfishPrivileges=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
        if "AssignedPrivileges" in patchData:
            for privilege in patchData["AssignedPrivileges"]:
                if not privilege in redfishPrivileges:
                    return (4, 400, "Bad Request-one or more Privileges are invalid", "",hdrs)

        # if here, all values are good. Update the accountServiceDb dict
        self.rolesDb[roleid]["AssignedPrivileges"]=patchData["AssignedPrivileges"]

        #xg5 note: service currently does not support oem privileges

        # write the rolesDb back out to the file
        dbDictJson=json.dumps(self.rolesDb, indent=4)
        with open( self.rolesDbFilePath, 'w', encoding='utf-8') as f:
            f.write(dbDictJson)

        return(0, 204, "No Content", "", hdrs)


    # ------------Accounts Collection Functions----------------


    # GET Accounts Collection
    def getAccountsCollectionResource(self, request ):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=["HEAD","GET","POST"],
                                     resource=self.accountsCollectionTemplate)
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # the routine copies a template file with the static redfish parameters
        # then it updates the dynamic properties from the accountsDb and accountsDict

        # copy the accountsCollection template file (which has an empty accounts array)
        resData2=dict(self.accountsCollectionTemplate)
        count=0
        # now walk through the entries in the accountsDb and built the accountsCollection Members array
        # note that the template starts out an empty array
        accountUriBase="/redfish/v1/AccountService/Accounts/"
        for accountEntry in self.accountsDb:
            # increment members count, and create the member for the next entry
            count=count+1
            memberUri=accountUriBase + accountEntry
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            resData2["Members"] = resData2["Members"] + newMember

        resData2["Members@odata.count"]=count

        # convert to json
        jsonResponseData2=json.dumps(resData2,indent=4)

        return(0, 200, "",  jsonResponseData2, hdrs)


    # GET Account Entry
    def getAccountEntry(self, request, accountid):
        # verify that the accountId is valid
        if accountid not in self.accountsDb:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found","",errhdrs)

        # first just copy the template sessionEntry resource
        resData=dict(self.accountEntryTemplate)

        # generate header info depending on the specific accountid
        #    accounts with property "Deletable"=False cannot be deleted
        #    for RedDrum, this includes accountid "root"
        #    for reference:   self.accountsDb[accountid]=
        #          {"UserName": username,    "Password": password, 
        #          "RoleId": roleId,    "Enabled": enabled,    "Deletable": True}
        if self.accountsDb[accountid]["Deletable"] is False:
            allowMethods="GetPatch"
        else:
            allowMethods=["HEAD","GET","PATCH","DELETE"]

        # check if account was locked but has now exceeded LockoutDuration
        #    if so, then unlock before returning data
        curTime=time.time()
        if self.accountsDict[accountid]["Locked"] is True:
            if( (curTime - self.accountsDict[accountid]["LockedTime"]) > self.accountServiceDb["AccountLockoutDuration"] ):
                # the lockout duration has expired.   unlock it.
                self.accountsDict[accountid]["Locked"]=False
                self.accountsDict[accountid]["LockedTime"]=0
                self.accountsDict[accountid]["FailedLoginCount"]=0
                self.accountsDict[accountid]["AuthFailTime"]=0

        # now overwrite the dynamic data from the accountsDb
        accountUri="/redfish/v1/AccountService/Accounts/" + accountid
        accountRoleId=self.accountsDb[accountid]["RoleId"]
        resData["@odata.id"]=accountUri
        resData["Id"]=accountid
        resData["Name"]="UserAccount"
        resData["Description"]="Local Redfish User Account"
        resData["Enabled"]=self.accountsDb[accountid]["Enabled"]
        resData["Password"]=None   # translates to Json: null
        resData["UserName"]=self.accountsDb[accountid]["UserName"]
        resData["RoleId"]=accountRoleId
        roleUri="/redfish/v1/AccountService/Roles/" + accountRoleId
        resData["Links"]={ "Role": {} }
        resData["Links"]["Role"]["@odata.id"]=roleUri

        # now overwrite the dynamic data from the sessionsDict
        # this is non-persistent account data
        resData["Locked"]=self.accountsDict[accountid]["Locked"]  

        # calculate eTag
        etagValue=self.calculateAccountEtag(accountid)

        respHdrs=self.hdrs.rfRespHeaders(request, contentType="json", allow=allowMethods,
                                     resource=self.accountEntryTemplate, strongEtag=etagValue)
        if request.method=="HEAD":
            return(0,200,"","",respHdrs)

        # convert to json
        jsonResponseData=json.dumps(resData,indent=4)

        #return etagHeader in response back to URI processing.  It will merge it
        return(0, 200, "",jsonResponseData, respHdrs)


    # general account service function to calculate the AccountEntry Etag
    #    this is a STRONG Etag
    #    Example:   etag="1ABCDEREDR"
    def calculateAccountEtag(self, accountid):
        enable   = self.accountsDb[accountid]["Enabled"]
        locked   = self.accountsDict[accountid]["Locked"]  
        username = self.accountsDb[accountid]["UserName"]
        password = self.accountsDb[accountid]["Password"]
        roleId   = self.accountsDb[accountid]["RoleId"]
        #etag="\"1234\""

        flag = 0
        if enable is True:
            flag = flag+1
        if locked is True:
            flag = flag+2
        m = hashlib.md5()
        m.update((username+password+roleId).encode('utf-8'))
        etagValue = str(flag) + m.hexdigest()
        return(etagValue)
        #etagHdr={"ETag": "\"" + m.hexdigest() + "\"" }
        #return(etagHdr)


    # POST Accounts
    # POST to Accounts collection  (add user)
    def postAccountsResource(self,request, postData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # first verify that the client didn't send us a property we cant write when creating the account
        # we need to fail the request if we cant handle any properties sent
        patchables=("UserName","Password","RoleId","Enabled","Locked")
        for prop in postData:
            if not prop in patchables:
                return (4, 400, "Bad Request-Invalid Post Property Sent", "",errhdrs)

        #get the data needed to create the account
        username=None
        password=None
        roleid=None
        enabled=True
        locked=False

        if( "UserName" in postData):
            username=postData['UserName']

        if("Password" in postData):
            password=postData['Password']

        if("RoleId" in postData):
            roleId=postData['RoleId']

        if("Enabled" in postData):
            enabled=postData['Enabled']

        if("Locked" in postData):
            locked=postData['Locked']

        # now check that all required on create properties were sent as post data
        if( (username is None) or (password is None) or (roleId is None ) ):
            return (4, 400, "Bad Request-Required On Create properties not all sent", "",errhdrs)

        # now verify that the Post data is valid

        # check if this username already exists
        for userId in self.accountsDb:
            if (username == self.accountsDb[userId]["UserName"]):
                return (4, 400, "Bad Request-Username already exists", "",errhdrs)

        # check if password length is less than value set in accountService MinPasswordLength
        if "MinPasswordLength" in self.accountServiceDb:
            if len(password) < self.accountServiceDb["MinPasswordLength"]:
                return (4, 400, "Bad Request-Password length less than min", "",errhdrs)
        if "MaxPasswordLength" in self.accountServiceDb:
            if len(password) > self.accountServiceDb["MaxPasswordLength"]:
                return (4, 400, "Bad Request-Password length exceeds max", "",errhdrs)
        # check if password meets regex requirements---no whitespace or ":"
        passwordMatchPattern="^[^\s:]+$"
        passwordMatch = re.search(passwordMatchPattern,password)
        if not passwordMatch:
            return (4, 400, "Bad Request-invalid password-whitespace or : is not allowed", "",errhdrs)

        # check if roleId does not exist
        #   check if the specified "RoleId" properly matches the RoleId property in RolesDb
        #   but if no RoleId property in RolesDb entry, check against the id of the role in RolesDb
        foundRoleId = False
        for roleid in self.rolesDb:
            if "RoleId" in self.rolesDb[roleid]:
                thisRoleIdName = self.rolesDb[roleid]["RoleId"]
            else:
                thisRoleIdName = roleId  # early Redfish model before RoleId prop existed in Roles
            # check if the specified roleId for the user matches one in the rolesDb 
            if thisRoleIdName == roleId:
                foundRoleId=True
                break    # so roleId will be the roleid value

        # if roleId was not found, return Bad Request error
        if foundRoleId is not True:
            return (4, 400, "Bad Request-roleId does not exist", "",errhdrs)

        # check if Enabled is a boul
        if (enabled is not True) and (enabled is not False):
            return (4, 400, "Bad Request-Enabled must be either True or False", "",errhdrs)
        # check if Locked  is a boul
        if locked is not False:
            return (4, 400, "Bad Request-Locked can only be set to False by user", "",errhdrs)

        # create response header data
        accountid=username
        locationUri="/redfish/v1/AccountService/Accounts/" + accountid

        # add the new account entry to the accountsDb
        self.accountsDb[accountid]={"UserName": username, "Password": password, 
                  "RoleId": roleId, "Enabled": enabled, "Deletable": True}

        # add the new account entry to the accountsDict
        dfltAccountDictEntry={ "Locked": False, "FailedLoginCount": 0, "LockedTime": 0, "AuthFailTime": 0 }
        self.accountsDict[accountid]=dfltAccountDictEntry

        # write the AccountDb back out to the file
        dbFilePath=os.path.join(self.rfr.varDataPath,"db", "AccountsDb.json")
        dbDictJson=json.dumps(self.accountsDb, indent=4)
        with open( dbFilePath, 'w', encoding='utf-8') as f:
            f.write(dbDictJson)
        
        # get the response data
        rc,status,msg,respData,respHdr=self.getAccountEntry(request, accountid)
        if( rc != 0):
            #something went wrong--return 500
            return(5, 500, "Error Getting New Account Data","",{})

        # calculate eTag
        etagValue=self.calculateAccountEtag(accountid)

        # get the response Header with Link, and Location
        respHeaderData=self.hdrs.rfRespHeaders(request, contentType="json", location=locationUri,
                                     resource=self.accountEntryTemplate, strongEtag=etagValue)

        #return to flask uri handler
        return(0, 201, "Created",respData,respHeaderData)



    # DELETE Account
    # delete the Account
    # all we have to do is verify the accountid is correct--
    # and then, if it is valid, delete the entry for that accountid from the accountsDb and accountsDict
    def deleteAccount(self, request, accountid):
        # generate the headers
        hdrs=self.hdrs.rfRespHeaders(request)

        # First, verify that the accountid is valid, 
        if accountid not in self.accountsDb:
            return(4, 404, "Not Found","",hdrs)

        # check if this is a deletable account
        if "Deletable" in self.accountsDb[accountid]:
            if self.accountsDb[accountid]["Deletable"] is True:
                del self.accountsDb[accountid]
            else:
                # get allow headers
                resp405Hdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow="GetPatch" )
                return(4, 405, "Method Not Allowed for this Account/URI","",resp405Hdrs)

        # delete the accountid entry from the accountsDict also
        if accountid in self.accountsDict:
            del self.accountsDict[accountid]

        # write the data back out to the accountService database file
        accountsDbJson=json.dumps(self.accountsDb,indent=4)
        filename="AccountsDb.json"
        with open( self.accountsDbFilePath, 'w', encoding='utf-8') as f:
            f.write(accountsDbJson)

        return(0, 204, "No Content","",hdrs)

    # Patch Account
    # patch an Account Entry 
    # used to update password or roleId, or unlock, or enable/disable the account
    #   self.accountsDict[accountid]=
    #       { "Locked": <locked>,  "FailedLoginCount": <failedLoginCnt>, "LockedTime": <lockedTimestamp>,
    #         "AuthFailTime": <authFailTimestamp> }
    def patchAccountEntry(self, request, accountid, patchData):
        # generate headers for 4xx error messages
        errhdrs = self.hdrs.rfRespHeaders(request )

        # First, verify that the accountid is valid, 
        if accountid not in self.accountsDb:
            return(4, 404, "Not Found", "", errhdrs)

        # 2nd if Password is in patch data, make sure that the request used https, or that credential update over http was enabled
        if "Password" in patchData:
            # procesa special cases for request coming in over http or https based on RedDrum.conf auth config settings
            requestHeadersLower = {k.lower() : v.lower() for k,v in request.headers.items()}
            #print("EEEEEEEE: hdrs: {}".format(requestHeadersLower))
            #if "X-rm-from-rproxy" in requestHeadersLower and requestHeadersLower["x-rm-from-rproxy"]=="https":
            if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTPS":
                # case: scheme is https,  so execute the API
                pass
            elif self.rdr.RedfishAllowUserCredUpdateOverHttp is True:
                # case: scheme=http,  but credential update over Http is allowed 
                pass
            else:
                # case: scheme=http, credential update over http is NOT allowed
                #  so return a 404-Not Found  status code
                return(4, 404, "404-Not Found-URI not supported over http", "", errhdrs)

        # verify that the patch data is good

        # first verify that ALL of the properties sent in patch data are patchable for redfish spec
        patchables=("Password","RoleId","Locked","Enabled","UserName")
        for prop in patchData:
            if( not prop in patchables ):
                return (4, 400, "Bad Request-one or more properties not patchable", "", errhdrs)

        # verify privilege is sufficient to change this property
        #    Privilege "ConfigureSelf" allows a user to change THEIR password, but no other property
        #    Privilege "ConfigureUsers" is required to change other users passwords

        # note that if "Password" is in patchData:
        # from auth wrapper, we know this user has either privilege ConfigureUsers or ConfigureSelf or both

        # Define which properties can be patched with different privileges
        #     Note: validPrivilegesList=("Login","ConfigureManager","ConfigureUsers","ConfigureSelf","ConfigureComponents")
        if "ConfigureUsers" in self.currentUserPrivileges:
            userHasPrivilegeToPatchProperties=["Password","RoleId","Locked","Enabled","UserName"]
        elif (self.currentUserAccountId == accountid) and ("ConfigureSelf" in self.currentUserPrivileges):     
            # user's accountId is same as target accountId and   the user that ConfigureSelf privilege to update their passwd
            userHasPrivilegeToPatchProperties=["Password"]
        else:  
            userHasPrivilegeToPatchProperties=[]
        
        # check if user does not have sufficient privilege to set ANY of the properties in the patch data
        # we must fail the ENTIRE patch if we can't update ANY of the properties
        #     otherwise, per redfish spec, we would need to generate extended data detailing which properties cant be updated and why
        for prop in patchData:
            if prop not in userHasPrivilegeToPatchProperties:
                self.rfr.logMsg("WARNING",
                   "403 Unauthorized-Patch Account: User does not have privilege to update account prop: {}".format(prop))
                return (4, 403, "User does not have privilege to update account data", "", errhdrs)

        # verify that the etag requirements are met
        # if request header had an If-Match: <etag>, verify the etag is still valid
        doIfMatchEtag=False
        if request.headers.get('if-match') is True:
            requestEtag = request.headers["if-match"]
            doIfMatchEtag=True

        if doIfMatchEtag is True:
            # first calculate strong eTag for this account
            currentEtag='"' + self.calculateAccountEtag(accountid) + '"'
            # verify they match
            if requestEtag  != currentEtag:
                self.rfr.logMsg("WARNING","412 If-Match Condition Failed-Patch Account")
                return (4, 412, "If-Match Condition Failed", "", errhdrs)

        # if Password was in patchData, verify value is good 
        if "Password" in patchData:
            password=patchData["Password"]
            # check if password length is less than value set in accountService MinPasswordLength
            if "MinPasswordLength" in self.accountServiceDb:
                if len(password) < self.accountServiceDb["MinPasswordLength"]:
                    self.rfr.logMsg("WARNING","400 Bad Request-Patch Account: Password length less than min")
                    return (4, 400, "Bad Request-Password length less than min", "", errhdrs)
            if "MaxPasswordLength" in self.accountServiceDb:
                if len(password) > self.accountServiceDb["MaxPasswordLength"]:
                    self.rfr.logMsg("WARNING","400 Bad Request-Patch Account: Password length exceeds max")
                    return (4, 400, "Bad Request-Password length exceeds max", "", errhdrs)

            # check if password meets regex requirements---no whitespace or ":"
            passwordMatchPattern="^[^\s:]+$"
            passwordMatch = re.search(passwordMatchPattern, password)
            if not passwordMatch:
                self.rfr.logMsg("WARNING","400 Bad Request-Patch Account: invalid password: whitespace or : is not allowed")
                return (4, 400, "Bad Request-invalid password-whitespace or : is not allowed", "", errhdrs)

            # generate the password hash
            # for sha512, this creates string like: "$6$R53DEEDrreeesg$REEDD/esEEFereg"  ie "$6$<salt>$<hash>"
            passwdHash = self.cryptContext.hash(password) 

        # if roleId was in patchData, verify value is good 
        if "RoleId" in patchData: 
            foundRoleId=False
            for roleid in self.rolesDb:
                if "RoleId" in self.rolesDb[roleid]:
                    thisRoleIdName = self.rolesDb[roleid]["RoleId"]
                else:
                    thisRoleIdName = roleId  # early Redfish model before RoleId prop existed in Roles
                # check if the specified roleId for the user matches one in the rolesDb 
                if thisRoleIdName == patchData["RoleId"]:
                    foundRoleId=True
                    break

            if foundRoleId is not True:
                self.rfr.logMsg("WARNING","400 Bad Request-Patch Account: roleId does not exist")
                return (4, 400, "Bad Request-roleId does not exist", "", errhdrs)

        # check if Enabled is a boul
        if "Enabled" in patchData: 
            if (patchData["Enabled"] is not True) and (patchData["Enabled"] is not False):
                self.rfr.logMsg("WARNING","400 Bad Request-Patch Account: Enabled must be either True or False")
                return (4, 400, "Bad Request-Enabled must be either True or False", "", errhdrs)

        # check if Locked is a legal value.   a user can only set locked to False, not true
        if "Locked" in patchData: 
            if patchData["Locked"] is not False:
                self.rfr.logMsg("WARNING",
                     "400 Bad Request-Patch Account: Locked can only be set to False by user")
                return (4, 400, "Bad Request-Locked can only be set to False by user", "", errhdrs)

        if "UserName" in patchData: 
            badName=False
            if ":" in patchData["UserName"]:
                badName=True
            for ch in patchData["UserName"]:
                if ch in string.whitespace:
                    badName=True
            if badName is True:
                self.rfr.logMsg("WARNING",
                     "400 Bad Request-Patch Account: UserName cannot contait : or whitespace")
                return (4, 400, "Bad Request-UserName cannot contain : or whitespace", "", errhdrs)

        # if here, all values are good. Update the account dict
        updateDb=False
        for prop in patchData:
            if (prop == "Locked"):
                # save new value to the volatile accountsDict
                self.accountsDict[accountid][prop]=patchData[prop]
            else:
                # save new value to the non-vol accountsDb and update the Db cache file
                updateDb=True
                # if updating the password, save hash instead of cleartext passwd
                if (prop == "Password"):
                    self.accountsDb[accountid][prop]=passwdHash
                else:
                    self.accountsDb[accountid][prop]=patchData[prop]

        # write the data back out to the accountService database file
        if updateDb is True:
            accountsDbJson=json.dumps(self.accountsDb,indent=4)
            filename="AccountsDb.json"
            with open( self.accountsDbFilePath, 'w', encoding='utf-8') as f:
                f.write(accountsDbJson)

        return(0, 204, "No Content","", errhdrs)

    def postPutAccountEntry(self, request, accountid):
        # the function returns a 405-Method not allowed
        # the only processing here is to determine the proper Allow header to return
        #   the specific Allow header list is a function of the accountid
        #   some accounts are not deletable

        if accountid not in self.accountsDb:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found","",errhdrs)

        if self.accountsDb[accountid]["Deletable"] is False:
            allowMethods="GetPatch"
        else:
            allowMethods=["HEAD","GET","PATCH","DELETE"],
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow=allowMethods)

        return(0, 405, "Method Not Allowed","", respHdrs)

    def postPutRoleEntry(self, request, roleid):
        # the function returns a 405-Method not allowed
        # the only processing here is to determine the proper Allow header to return
        #   the specific Allow header list is a function of the roleid
        #   some roles are not deletable or patchable

        if roleid not in self.rolesDb:
            # generate error header for 4xx errors
            errhdrs=self.hdrs.rfRespHeaders(request)
            return(4, 404, "Not Found", "",errhdrs)

        if self.rolesDb[roleid]["IsPredefined"] is True:
            # pre-defined roles cannot be deleted or modified
            allowMethods="Get"
        else:
            allowMethods=["HEAD","GET","PATCH","DELETE"],
        respHdrs=self.hdrs.rfRespHeaders(request, contentType="raw", allow=allowMethods)

        return(0, 405, "Method Not Allowed","", respHdrs)

# end
# NOTES TODO
# if you delete a role, verify that no user is assigned that role
# search for other TODOs
