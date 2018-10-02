
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

from flask import Flask
from flask import request, Response, send_from_directory 
import json
import os,re
from .flask_redfish_auth import RfHTTPBasicOrTokenAuth
from .authenticate import rfRegisterBasicAuthVerify
from .authenticate import rfRegisterTokenAuthVerify
from .redfish_headers import rfcheckHeaders
from flask import g
from flask import make_response

# Base RedDrum Flask startup class
#   rdr is a class with global data.
#   it includes rdr.root which is the root resource that everything hangs below
#   

# -----------------------------------------------------------------------
def rdStart_RedDrum_Flask_app(rdr):
    rfr = rdr  

    rdr.logMsg("INFO"," Initializing Flask URIs ")

    # =======================================================================
    # instantiate the flask app class
    #    usage:  app = Flask(__name__, static_folder=staticPath)
    app = Flask(__name__)

    # =======================================================================
    # create auth class that does basic or redifish session auth
    auth=RfHTTPBasicOrTokenAuth()

    # =======================================================================
    # register the authentication callback routines 
    # these functions are in ./authenticate.py
    rfRegisterBasicAuthVerify(auth,rdr)
    rfRegisterTokenAuthVerify(auth,rdr)


    # =======================================================================
    # Define the default "After Request" processing method
    #    This is a flask hook for after request. 
    #    It is invoked for every post-request.
    @app.after_request
    def after_request_call(response):
        # reset the currentUserId and currentUserPrivileges
        rfr.root.accountService.currentUserId=None
        rfr.root.accountService.currentUserPrivileges=None
        return response


    # =======================================================================
    # Register The RedDrum Redfish URI APIs for Flask
    #   Example usage for resources under root:
    #      rc,statusCode,errString,resp,hdrs=rdr.root.WHATEVER(request)
    #      return(resp,statusCode,hdrs)

    # -----------------------------------------------------------------------
    # Service Root APIs

    # Get versions
    # GET /redfish      -- returns the versions array
    #  -no auth, json 
    @app.route("/redfish",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    def rfGetVersions():
        rc,statusCode,errString,resp,hdrs=rdr.root.serviceVersions.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # Get Root
    # GET /redfish/v1    -- returns the service root
    #  -no auth, json,   Note that this route must be "BEFORE" the /redfish/v1/ API w/ trailing /
    @app.route("/redfish/v1", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    def rfServiceRoot():
        rc,statusCode,errString,resp,hdrs=rdr.root.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get Root
    # GET /redfish/v1/   
    #  -no auth,  json 
    @app.route("/redfish/v1/", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    def rfServiceRoot1():
        rc,statusCode,errString,resp,hdrs=rdr.root.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get Odata
    # GET /redfish/v1/odata    
    #  -no auth, json 
    @app.route("/redfish/v1/odata",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    def rfOdataServiceDoc():
        rc,statusCode,errString,resp,hdrs=rdr.root.odata.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get Metadata
    # GET /redfish/v1/$metadata    
    #  -no auth, xml 
    @app.route("/redfish/v1/$metadata",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr,contentType="xml") 
    def rfOdataMetadata():
        rc,statusCode,errString,resp,hdrs=rdr.root.metadata.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # ----------------------------------------------------------------
    # RedDrum Info API -- not defined by Redfish, and not linked anywhere in API
    #    returns some info about the implementation and configuration

    # Get RedDrumInfo
    # GET /redfish/v1/RedDrumInfo    
    #  -auth, json
    @app.route("/redfish/v1/RedDrumInfo", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetRedDrumServiceInfo():
        rc,statusCode,errString,resp,hdrs=rdr.root.redDrumServiceInfo.getResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)
    

    # -----------------------------------------------------------------------
    # Registries and JsonSchema APIs

    # Get Registries
    # GET /redfish/v1/Registries    
    #  -auth, json 
    @app.route("/redfish/v1/Registries",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfRegistriesCollection():
        rc,statusCode,errString,resp,hdrs=rdr.root.registries.getRegistriesCollection(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get Registry
    # GET /redfish/v1/Registries/<registry>    
    #  -auth, json 
    @app.route("/redfish/v1/Registries/<registryId>",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfRegistriesFile(registryId):
        rc,statusCode,errString,resp,hdrs=rdr.root.registries.getRegistriesFile(request,registryId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # Get JsonSchemas
    # GET /redfish/v1/JsonSchemas    
    #  -auth, json
    @app.route("/redfish/v1/JsonSchemas",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfJsonSchemasCollection():
        rc,statusCode,errString,resp,hdrs=rdr.root.jsonSchemas.getJsonSchemaCollection(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get JsonSchema
    # GET /redfish/v1/JsonSchemas/<jsonSchemaId>    
    #  -auth, json 
    @app.route("/redfish/v1/JsonSchemas/<jsonSchemaId>",methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfJsonSchemaFile(jsonSchemaId):
        rc,statusCode,errString,resp,hdrs=rdr.root.jsonSchemas.getJsonSchemaFile(request,jsonSchemaId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)



    # -----------------------------------------------------------------------
    # APIs to read one of the static DMTF-defined json-formatted Redfish schema files
    #   this is not strictly part of Redfish but the JsonSchema files we generate point to these APIs
    #   this GET returns the full DMTF-defined schema file

    # Get SchemaFile
    # GET /redfish/v1/Schemas/<schemaFile>    
    #  -unauthenticated static, json or xml. flask generates Content-Type
    @app.route("/redfish/v1/schemas/<schemaFile>",methods=['GET'])
    @rfcheckHeaders(rdr)
    def rfGetSchemaFile(schemaFile):
        return send_from_directory( rdr.schemasPath, schemaFile, add_etags=False)

    # Get RegistryFile
    # GET /redfish/v1/Schemas/Registries/<registryFile>    
    @app.route("/redfish/v1/schemas/registries/<registryFile>",methods=['GET'])
    @rfcheckHeaders(rdr)
    def rfGetRegistryFile(registryFile):
        regPath=os.path.join(rdr.schemasPath, "registries")
        return send_from_directory( regPath, registryFile, add_etags=False )


    # -----------------------------------------------------------------------
    # SessionService URIs

    # Get SessionService
    # GET /redfish/v1/SessionService
    #   -auth, generated from template and sessionServiceDb
    @app.route("/redfish/v1/SessionService", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSessionService():
        rc,statusCode,errString,resp,hdrs=rdr.root.sessionService.getSessionServiceResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Patch SessionService
    # PATCH /redfish/v1/SessionService
    #    -auth, updates sessionServiceDb
    @app.route("/redfish/v1/SessionService", methods=['PATCH'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfPatchSessionService():     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rfr.root.sessionService.patchSessionServiceResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get Sessions
    # GET /redfish/v1/SessionService/Sessions  --get sessions collection
    #    -auth, generated from template and sessionsDict    
    @app.route("/redfish/v1/SessionService/Sessions", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSessions():
        rc,statusCode,errString,resp,hdrs=rdr.root.sessionService.getSessionsCollectionResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)
    
    # Get Session
    # GET /redfish/v1/SessionService/Sessions/<sessionid> --get session entry
    #    -auth, generated from template and sessionsDict
    @app.route("/redfish/v1/SessionService/Sessions/<sessionid>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSessionsEntry(sessionid):
        rc,statusCode,errString,resp,hdrs=rfr.root.sessionService.getSessionEntry(request, sessionid)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Post Sessions,  SessionLogin API
    # POST to /redfish/v1/SessionService/Sessions
    #  -No auth required,  returns created json Session resource, 
    #  -since this is an unauthenticated API, login requests using http will be redirected to https (if https is enabled)
    @app.route("/redfish/v1/SessionService/Sessions", methods=['POST'])
    @rfcheckHeaders(rfr)
    def rfLogin():
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.sessionService.postSessionsResource(request,rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)
        #return(resp,statusCode,hdrs)

    # Delete Session,  SessionLogout API
    # DELETE /redfish/v1/SessionService/Sessions/<sessionid> 
    #   -auth, -authorizationInsideAPI.   removes the session entry from the sessionsDict
    @app.route("/redfish/v1/SessionService/Sessions/<sessionid>", methods=['DELETE'])
    @rfcheckHeaders(rfr)
    # *** API REQUIRES ADDITIONAL AUTHORIZATION INSIDE API:  users with Login privilege can only delete their own session
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"],["Login"]]) 
    def rfSessionLogout(sessionid):
        rc,statusCode,errString,resp,hdrs=rfr.root.sessionService.deleteSession(request, sessionid)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # -----------------------------------------------------------------------
    #  EventService URIs

    # Get EventService
    # GET /redfish/v1/EventService   --get Event service
    #    -auth, json
    @app.route("/redfish/v1/EventService", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetEventService():
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.getEventServiceResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # ------------------------------------------------------------
    # Event Service/ Subscriptions APIs

    # Get Subscriptions
    # GET /redfish/v1/EventService/Subscriptions -- get Subscription collection
    # Privilege is "Login" or Ability to log into the service and read resources
    #    -auth, json
    @app.route("/redfish/v1/EventService/Subscriptions", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSubscriptions():
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.getEventSubscriptionsResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

#GETS for EventService will have privilege "Login"
#dmtf github redfish tree registeries
#PrivilegeRegisteries
#Entity is EventService
#oPATCH is Prvilige ConfigureManager
#Review privilges in the spec
#Look at SessionService for headers
    # Get Subscription Entry
    # GET /redfish/v1/EventService/Subscriptions/<subscriptionId>  -- get Subscription entry
    #    -auth, json
    @app.route("/redfish/v1/EventService/Subscriptions/<subscriptionId>", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSubscriptionEntry(subscriptionId):
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.getSubscriptionEntry(request, subscriptionId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)


    # Patch EventService
    # PATCH /redfish/v1/EventService   --patch event service
    #    -auth, update patch properties in EventService database file
    #    -returns 204-No Content
    @app.route("/redfish/v1/EventService", methods=['PATCH'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfPatchEventService():     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.patchEventServiceResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # POST to Event Subscriptions -- return 405 and proper allow header for POST of a subscriptionId
    # POST /redfish/v1/EventService/Subscriptions
    @app.route("/redfish/v1/EventService/Subscriptions", methods=['POST'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfPostPutSubscriptionEntry405handler():     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.postSubscriptionResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # Delete Subscription -- delete an subscription
    # DELETE /redfish/v1/EventService/Subscriptions/<subscriptionId> 
    #   -auth,  
    @app.route("/redfish/v1/EventService/Subscriptions/<subscriptionId>", methods=['DELETE'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfDeleteSubscription(subscriptionId):
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.deleteSubscriptionEntry(request, subscriptionId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # Patch Subscription  -- update a Subscription entry -- patch 
    # PATCH /redfish/v1/EventService/Subscriptions/<subscriptionId>
    #    -auth, write to a property in the Subscription
    @app.route("/redfish/v1/EventService/Subscriptions/<subscriptionId>", methods=['PATCH'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureComponents"]])
    def rfPatchSubscriptionEntry(subscriptionId):     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.patchSubscriptionEntry(request, subscriptionId, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # POST test event
    # TODO check privileges
    # POST /redfish/v1/EventService/Actions/EventService.SendTestEvent
    @app.route("/redfish/v1/EventService/Actions/EventService.SendTestEvent", methods=['POST'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfEventTestEntry():     
        rdata=request.get_json(cache=True)
        #rc,statusCode,errString,resp,hdrs=rdr.root.eventService.sendTestEvent(request, rdata)
        rc,statusCode,errString,resp,hdrs=rdr.root.eventService.stubResponse()
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return(resp,statusCode,hdrs)

    # -----------------------------------------------------------------------
    #  AccountService URIs

    # Get AccountService
    # GET /redfish/v1/AccountService   --get account service
    #    -auth, json
    @app.route("/redfish/v1/AccountService", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetAccountService():
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.getAccountServiceResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Patch AccountService
    # PATCH /redfish/v1/AccountService   --patch account service
    #    -auth, update patch properties in AccountService database file
    #    -returns 204-No Content
    @app.route("/redfish/v1/AccountService", methods=['PATCH'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureUsers"]])
    def rfPatchAccountService():     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.patchAccountServiceResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # ------------------------------------------------------------
    # Account Service/ Roles APIs

    # Get RolesCollection
    # GET /redfish/v1/AccountService/Roles -- get roles collection
    #    -auth, json
    @app.route("/redfish/v1/AccountService/Roles", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetRoles():
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.getRolesCollectionResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

     #TODO look for subscriptionId
     # Get Role
     # GET /redfish/v1/AccountService/Role/<roleId>  -- get role entry
     #    -auth, json


    # Get Role
    # GET /redfish/v1/AccountService/Role/<roleId>  -- get role entry
    #    -auth, json
    @app.route("/redfish/v1/AccountService/Roles/<roleId>", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetRoleId(roleId):
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.getRoleEntry(request, roleId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)
        
    # Post RolesCollection,  add a custom Role
    # POST to /redfish/v1/AccountService/Roles
    #  -auth required,  adds another role entry to the rolesDb
    @app.route("/redfish/v1/AccountService/Roles", methods=['POST'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfPostRoles():
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.postRolesResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Delete Role -- delete a custom role
    # DELETE /redfish/v1/AccountService/Roles/<roleid> 
    #   -auth,  
    @app.route("/redfish/v1/AccountService/Roles/<roleid>", methods=['DELETE'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfDeleteRole(roleid):
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.deleteRole(request, roleid)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Patch Role  -- update a custom role entry -- patch user account
    # PATCH /redfish/v1/AccountService/Roles/<roleId>
    #    -auth, write to a property in the role
    @app.route("/redfish/v1/AccountService/Roles/<roleId>", methods=['PATCH'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureManager"]])
    def rfPatchRoleEntry(roleId):     
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.patchRoleEntry(request, roleId, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # POST, PUT  RoleId  -- return 405 and proper allow header for POST an PUT of a roleId
    # POST /redfish/v1/AccountService/Roles/<roleId>
    # PUT  /redfish/v1/AccountService/Roles/<roleId>
    @app.route("/redfish/v1/AccountService/Roles/<roleId>", methods=['POST','PUT'])
    def rfPostPutRoleEntry405handler(roleId):     
        #rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rdr.root.accountService.postPutRoleEntry(request, roleId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # ------------------------------------------------------------
    # Account Service/ Accounts APIs

    # Get Accounts
    # GET /redfish/v1/AccountService/Accounts -- get accounts collection
    #    -auth, json
    @app.route("/redfish/v1/AccountService/Accounts", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetAccounts():
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.getAccountsCollectionResource(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)
    
    # Get Account
    # GET /redfish/v1/AccountService/Accounts/<accountId>  -- get account entry
    #    -auth, json
    @app.route("/redfish/v1/AccountService/Accounts/<accountId>", methods=['GET','HEAD'])
    @rfcheckHeaders(rdr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetAccountId(accountId):
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.getAccountEntry(request, accountId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # add a user
    # POST to /redfish/v1/AccountService/Accounts
    #  -auth required,  adds another user to the accountsDb and accountsDict
    @app.route("/redfish/v1/AccountService/Accounts", methods=['POST'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureUsers"]])
    def rfPostAccounts():
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.postAccountsResource(request, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Delete Account  -- delete a user
    # DELETE /redfish/v1/AccountService/Accounts/<accountId> 
    #   -auth,  removes the account entry from the accountsDb and accountsDict
    @app.route("/redfish/v1/AccountService/Accounts/<accountId>", methods=['DELETE'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureUsers"]])
    def rfDeleteAccount(accountId):
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.deleteAccount(request, accountId)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Patch Account -- update a user account-- patch user account
    # PATCH /redfish/v1/AccountService/Accounts/<accountId>
    #    -auth,  
    @app.route("/redfish/v1/AccountService/Accounts/<accountId>", methods=['PATCH'])
    # *** API REQUIRES ADDITIONAL AUTHORIZATION INSIDE API:  users with configureSelf privilege can update only their passwords
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureUsers"],["ConfigureSelf"]])
    def rfPatchAccountEntry(accountId):
        rdata=request.get_json(cache=True)
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.patchAccountEntry(request, accountId, rdata)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # POST, PUT Account -- return 405 and proper allow header for POST an PUT of an account
    # POST /redfish/v1/AccountService/Accounts/<accountId>
    # PUT  /redfish/v1/AccountService/Accounts/<accountId>
    @app.route("/redfish/v1/AccountService/Accounts/<accountId>", methods=['POST','PUT'])
    def rfPostPutAccountEntry405handler(accountId):
        #rdata=request.get_json(cache=True) # since a post or put may sent request data
        rc,statusCode,errString,resp,hdrs=rfr.root.accountService.postPutAccountEntry(request, accountId )
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # Top-level Systems, Chassis, Managers Collection GETs

    # GET Systems
    # GET /redfish/v1/Systems
    #  -auth, json
    @app.route("/redfish/v1/Systems", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfSystems():
        rc,statusCode,errString,resp,hdrs=rfr.backend.systems.getSystemsCollection(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # GET Chassis
    # GET /redfish/v1/Chassis
    #  -auth, json
    @app.route("/redfish/v1/Chassis", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfChassis():
        rc,statusCode,errString,resp,hdrs=rfr.backend.chassis.getChassisCollection(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # GET Managers
    # GET /redfish/v1/Managers
    #  -auth, json
    @app.route("/redfish/v1/Managers", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfManagers():
        rc,statusCode,errString,resp,hdrs=rfr.backend.managers.getManagersCollection(request)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # -----------------------------------------------------------------------
    # Systems, Chassis, Managers   Resource GETs, PATCHs

    # GET System
    # GET /redfish/v1/Systems/<sysid>  -- get system entry
    #    -auth, json
    @app.route("/redfish/v1/Systems/<path:urlSubPath>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSystemsResource(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.systems.processSystemsResource(request, urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    @app.route("/redfish/v1/Systems/<path:urlSubPath>", methods=['PATCH'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureComponents"]])
    def rfPatchSystemsResource(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.chassis.processSystemsResource(request,urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # GET Chassis
    # GET /redfish/v1/Chassis/<chassisid>  -- get account entry
    #    -auth, json
    @app.route("/redfish/v1/Chassis/<path:urlSubPath>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetChassisResource(urlSubPath):
        print("at URLS: subpath: {}".format(urlSubPath))
        rc,statusCode,errString,resp,hdrs=rfr.backend.chassis.processChassisResource(request,urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    @app.route("/redfish/v1/Chassis/<path:urlSubPath>", methods=['PATCH'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureComponents"]])
    def rfPatchChassisResource(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.chassis.processChassisResource(request,urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # GET Manager
    # GET /redfish/v1/Managers/<mgrid>  -- get account entry
    #    -auth, json
    @app.route("/redfish/v1/Managers/<path:urlSubPath>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetManagers(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.managers.processManagersResource(request, urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    @app.route("/redfish/v1/Managers/<path:urlSubPath>", methods=['PATCH'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["ConfigureComponents"]])
    def rfPatchManagersResource(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.chassis.processManagersResource(request,urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)


    # -----------------------------------------------------------------------
    # API for local schemastores -- these can be localized to point to various aggregated BMC schemaStores
    @app.route("/redfish/v1/SchemaStores/<path:urlSubPath>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetSchemaStores(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.processSchemaStores(request, urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # -----------------------------------------------------------------------
    # API for local generic Location Header links
    #   if a client replays a location header link starting w/ /redfish/v1/LocationUris/...,
    #      it will be unlocalized and sent to the BMC that originated the link with the correct path.
    @app.route("/redfish/v1/LocationUris/<path:urlSubPath>", methods=['GET','HEAD'])
    @rfcheckHeaders(rfr)
    @auth.rfAuthRequired(rdr, privilege=[["Login"]])
    def rfGetLocationUris(urlSubPath):
        rc,statusCode,errString,resp,hdrs=rfr.backend.processLocationUris(request, urlSubPath)
        resp,statusCode,hdrs=rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs)
        return rfMakeResponse(resp,statusCode,hdrs)

    # -----------------------------------------------------------------------
    # Internal RedDrum APIs used by backends

    # Post to Backend 
    # POST /RedDrum/Backend/<apiId>
    @app.route("/RedDrum/Backend/<apiId>", methods=['POST'])
    def rdPostBackendApi(apiId):
        rdata=request.get_json(cache=True)     
        rc,statusCode,errString,resp,hdrs=rfr.backend.postBackendApi(request, apiId, rdata)
        return rfMakeResponse(resp,statusCode,hdrs)

    # Get to Backend 
    # GET /RedDrum/Backend/<apiId>
    @app.route("/RedDrum/Backend/<apiId>", methods=['GET'])
    def rdGetBackendApi(apiId):
        rc,statusCode,errString,resp,hdrs=rfr.backend.getBackendApi(request, apiId)
        return rfMakeResponse(resp,statusCode,hdrs)


    # -----------------------------------------------------------------------
    #END file redfishURIs


    # ======================================================================
    # start Flask REST engine running
    rfr.logMsg("INFO"," Running Flask App ")

    app.run(host=rfr.rdHost, port=rfr.rdPort)

    #never returns


# ======================================================================
# Per API Error Processing
def rfMakeResponse(resp,statusCode,hdrs):
    response  = make_response(resp,statusCode,hdrs)
    response.autocorrect_location_header = False
    return response

def rfProcessErrors(rdr,request,rc,statusCode,errString,resp,hdrs):
    if rc==0:  
        if rdr.debug is True:
            if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTPS":
                scheme="https"
            else:
                scheme="http"
            print("API_OK: Method: {}, Scheme: {}, Path: {}, rc: {}, status_code: {}: {}".format(
                  request.method,scheme,request.path,rc,statusCode,errString))
        return(resp,statusCode,hdrs)
    else:
        if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTPS":
            scheme="https"
        else:
            scheme="http"
        errMsg=" Method: {}, Scheme: {}, Path: {}, rc: {}, status_code: {}: {}".format(request.method,scheme,request.path,rc,statusCode,errString)
        rdr.logMsg("ERROR",errMsg)
        # add extended error message here
        return(resp,statusCode,hdrs)

# ======================================================================
# Flask Notes for Reference
#     reference source links:
#     http://docs.python-requests.org/en/v0.10.6/api/
#     http://flask.pocoo.org/docs/0.10/quickstart/
#     app.run(host="0.0.0.0") # run on all IPs
#     run(host=None, port=None, debug=None, **options)
#       host=0.0.0.0 server avail externally -- all IPs
#       host=127.0.0.1 is default
#       port=5001 default, or port defined in SERVER_NAME config var
# ======================================================================
