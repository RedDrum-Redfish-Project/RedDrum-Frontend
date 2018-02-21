
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

# Contains routines used to verify auth credentials
# These routines are called from rfApi_RackManager() in redfishURIs.py
# They registered the callback routines for validating Basic and Token auth credentials
#   using whatever method is implemented for the service

def rfRegisterBasicAuthVerify( auth, rfr ):
    #define basic auth decorator used by flask
    # for RMv06 basic auth, we only support user=root, passwd=calvin
    @auth.verify_basic_password
    def  verifyRfPasswd(user,passwd, privilege="None"):
        rc,errMsg,accountid,roleId,userPrivileges=rfr.root.accountService.getAccountAuthInfo(user,passwd)
        
        if( rc == 0 ): #authenticated:
            check = rfCheckPrivileges( userPrivileges, privilege)
            if check is False:
                return ("403")
            else:
                # set currentUserId and currentUserPrivileges for this user
                rfr.root.accountService.currentUserAccountId=accountid
                rfr.root.accountService.currentUserPrivileges=userPrivileges
                return("200")        
        else:  #unauthentication failed
            return("401")



def rfRegisterTokenAuthVerify( auth, rfr ):
    @auth.verify_token
    def  verifyRfToken(auth_token, privilege="None"):
        rc,errMsg,sessionid,authtoken,userprivileges,accountid,username = rfr.root.sessionService.getSessionAuthInfo(authtoken=auth_token)
        if( rc == 0 ):
            check = rfCheckPrivileges( userprivileges, privilege)
            if check is False:
                return ("403")
            else:
                # set currentUserId and currentUserPrivileges for this user
                rfr.root.accountService.currentUserAccountId=accountid
                rfr.root.accountService.currentUserPrivileges=userprivileges
                return("200")
        else:
            return("401")  #unauthorized user



# Check if the user has sufficient privileges to execute the API 
# The user privileges are a list of privileges.
# The API privileges are a nested set of privileges of form: 
#      privilege=[ ["privA",privB"],["privC", "privD"] ]
# This means the user must have (privA && privB) || (privC && privD) in their priv array
# Normally it is simple

def rfCheckPrivileges( userPrivileges, apiPrivileges ):
    for privSublist in apiPrivileges:          # go through each sublist of required privileges
        authorized=True                        # 
        for priv in privSublist:               # go throuh each required privilege in sublist
            if priv not in userPrivileges:     #   user must have all of the privileges in the sublist
                authorized=False               #   so mark auth false if any mismatch
                break                          #   break out of for privSublist in privilege
        if authorized is True:                 # if we authorized on 1st sublist, no need to proceed
            break
    return( authorized)


