
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

#adapted from:
#    flask_httpauth
#    ==================
#    This module provides Basic and Digest HTTP authentication for Flask routes.
#    :copyright: (C) 2014 by Miguel Grinberg.
#    :license:   MIT, see LICENSE for more details, 
#        at https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/master/LICENSE
#
#    see documentation at:    http://flask.pocoo.org/snippets/8/
#    code and docs at:       https://github.com/miguelgrinberg/flask-httpauth/
#
#**** modified to implement EITHER Redfish Token Auth or Basic Auth
#    this file is imported by: catfishURIs.py
#
#  Usage:  In *Main.py: see this flow below in redfishURIs.py
#        ... in redfishURIs.py
#        from .flask_redfish_auth import RfHTTPBasicOrTokenAuth
#        ...
#        #create instance of the modified Basic or Redfish Token auth
#        #   this is what is in this file
#        auth=RfHTTPBasicOrTokenAuth
#        
#        #define basic auth decorator used by flask
#        @auth.verify_basic_password
#        def verifyRfPasswd(user,passwd):
#        ...
#        
#        #define Redfish Token/Session auth decorator used by flask
#        @auth.verify_token
#        def verifyRfToken(auth_token):
#        ...
#
#        @app.route("/api", methods=['GET'])
#        @auth.rfAuthRequired
#        def api()
#        ...

from functools import wraps
from flask import request, Response

from urllib.parse import urlparse, urlunparse

#this is the Base HTTP Auth class that is used to derive the Redfish "Basic or Token Auth" class
class HTTPAuth(object):
    def __init__(self, scheme=None, realm=None):
        def default_get_password(userx):
            return None

        def default_basic_auth_error():
            return "Unauthorized Access"
        
        def default_token_auth_error():
            return "Unauthorized Access. Invalid authentication token"
        
        self.scheme = scheme
        self.realm = realm or "Authentication Required"
        self.get_password(default_get_password)
        self.basic_error_handler(default_basic_auth_error)
        self.token_error_handler(default_token_auth_error)


    def get_password(self, f):
        self.get_password_callback = f
        return f
    
    def token_error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            if type(res) == str:
                res = make_response(res)
                res.status_code = 401
            return res
        self.auth_token_error_callback = decorated
        return decorated
    
    def basic_error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            if type(res) == str:
                res = make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = self.authenticate_header()
            return res
        self.auth_basic_error_callback = decorated
        return decorated

    def makeErrHdrs(self,rdr):
        hdrs=dict()
        # std odata header
        hdrs['OData-Version']='4.0'
        # Server header
        if rdr.HttpHeaderServer is not None:
            hdrs['Server'] = rdr.HttpHeaderServer
        else:
            pass # let Apache fill-in the Server header 
        # Cach-Control
        if rdr.HttpHeaderCacheControl is not None:
            hdrs['Cache-Control'] = rdr.HttpHeaderCacheControl
        else:
            pass  # use default Apache behavior
        # Access-Control-Allow-Origin:  
        if rdr.HttpHeaderAccessControlAllowOrigin is not None:
            if rdr.HttpHeaderAccessControlAllowOrigin == "FromOrigin":
                requestHeadersLower = {k.lower() : v for k,v in request.headers.items()}
                if 'origin' in requestHeadersLower:
                    hdrs['Access-Control-Allow-Origin'] = requestHeadersLower['origin']
            else:
                hdrs['Access-Control-Allow-Origin'] = rdr.HttpHeaderAccessControlAllowOrigin
        else:
            pass  # don't create this header--use default Apache behavior 
        # Content-Type
        hdrs['Content-Type'] = "charset=utf-8"

        return(hdrs)

    def processErrors(self, rdr, request, errMsg, statusCode):
        print("ERROR: rfAuthRequired: method: {}, path: {}, statusCode: {}: {}".format(
                request.method, request.path, statusCode, errMsg))
        return(0)

    #for redfish, we need to hook this to check if its token auth before trying basic auth
    def rfAuthRequired(self, rdr, privilege=None):
        def rfAuthRequiredCallable(f ):
            @wraps(f)
            def decorated(*args, **kwargs):
                auth = request.authorization
                #print("EEEEE-AUTH: in rfAuthRequired--privilege: {}".format(privilege))
                #print("EEEEE-AUTH: headers: {}".format(request.headers))
                # We need to ignore authentication headers for OPTIONS to avoid  unwanted interactions with CORS.
                # Chrome and Firefox issue a preflight OPTIONS request to check Access-Control-* headers, 
                #     and will fail if it returns 401.

                if request.method != 'OPTIONS':
                    # auth is None if the Basic auth header didn't come in the request
                    found_token=False
                    auth_token=None
                    authType=None 
                    if( auth is None ):
                        #check if we have a redfish auth token
                        ###print("auth is None")
                        auth_token=request.headers.get("X-Auth-Token")
                        ###print("token={}".format(auth_token))
                        if( auth_token is not None):
                            found_token=True
                            authType="SessionAuth"
                    else: 
                        authType="BasicAuth"

                    # at this point: authType is oneOf: None, "BasicAuth", "SessionAuth"

                    if privilege is None:   
                        # this is only true if no privilege array is passed in
                        # this is equivalent to not calling the rfAuthRequired function at all
                        pass
                    elif rdr.RedfishAllowAuthNone is True:
                        # this is the global that effectively turns-off all authentication and authroization checking
                        # all APIs are executed as if you were root
                        pass
                    else:
                        #if scheme is 'http':
                        if "X-Rm-From-Rproxy" in request.headers and request.headers["X-Rm-From-Rproxy"]=="HTTP": 
                            #print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
                            # Check if Authenticated APIs over http are allowed at all
                            if rdr.RedfishAllowAuthenticatedAPIsOverHttp is False:
                                errhdrs=self.makeErrHdrs(rdr)
                                statusCode=404
                                errMsg="404-authenticated API over HTTP not allowed "
                                self.processErrors(rdr, request, errMsg, statusCode)
                                return Response('', statusCode, errhdrs)
                            # Check if the request auth type is Basic and if so whether Basic over HTTP is allowed:
                            if authType=="BasicAuth":
                                if rdr.RedfishAllowBasicAuthOverHttp is False:
                                    errhdrs=self.makeErrHdrs(rdr)
                                    statusCode=404
                                    errMsg="404-BasicAuth over HTTP not allowed "
                                    self.processErrors(rdr, request, errMsg, statusCode)
                                    return Response('', statusCode, errhdrs)

                        # Authenticate session auth
                        if authType=="SessionAuth":
                            authOk=self.verify_token_callback(auth_token,privilege=privilege) 
                            ###print("verify_token={}".format(authOk))
                            if( authOk != '200'):
                                #we had an auth token, but it didn't validate, return error
                                if authOk == '401':
                                    # 401-Authentication Failed. dont send WWW-Authenticate header
                                    errhdrs=self.makeErrHdrs(rdr)
                                    statusCode=401
                                    errMsg="401-SessionAuth failed authentication"
                                    self.processErrors(rdr, request, errMsg, statusCode)
                                    return Response('', statusCode, errhdrs)
                                else:
                                    # 403-Authorization Failed
                                    errhdrs=self.makeErrHdrs(rdr)
                                    statusCode=403
                                    errMsg="403-sessionAuth failed Authorization"
                                    self.processErrors(rdr, request, errMsg, statusCode)
                                    return Response('', statusCode, errhdrs)

                        # Authenticate Basic auth
                        elif authType=="BasicAuth":
                            if auth:
                                password = self.get_password_callback(auth.username)
                            else:
                                password = None
                            ###print("basic auth: auth={}, pwd={}".format(auth,password))
                            basicAuthOk = self.authenticate(auth, password, privilege=privilege)
                            if( basicAuthOk != '200'):
                                if basicAuthOk == '401':
                                    #401-Authentication Failed. dont send WWW-Authenticate header
                                    errhdrs=self.makeErrHdrs(rdr)
                                    statusCode=401
                                    errMsg="401-BasicAuth failed Authentication"
                                    self.processErrors(rdr, request, errMsg, statusCode)
                                    return Response('', statusCode, errhdrs)
                                else:
                                    #403-Authroziation Failed
                                    errhdrs=self.makeErrHdrs(rdr)
                                    statusCode=403
                                    errMsg="403-BasicAuth failed Authorization"
                                    self.processErrors(rdr, request, errMsg, statusCode)
                                    return Response('', statusCode, errhdrs)

                        # request had neither a Session or Basic Auth header
                        # in this case, we follow standard BasicAuth protocol and return a WWW-Authenticate header w/ 401 
                        else:  # authType is None: no authentication header was sent
                            #in this case, we send back a WWW-Authenticate header (if we are supporting BasicAuth)
                            errhdrs=self.makeErrHdrs(rdr)
                            errhdrs['WWW-Authenticate'] = "Basic"
                            #401-Authentication Failed-requested
                            statusCode=401
                            errMsg="401-No Auth Header, return 401 with WWW-Authenticdate Header"
                            self.processErrors(rdr, request, errMsg, statusCode)
                            return Response('', statusCode, errhdrs)

                return(f(*args, **kwargs))
            return(decorated)
        return rfAuthRequiredCallable


    def username(self):
        if not request.authorization:
            return ""
        return request.authorization.username


# this class is derived from HTTPAuth above
class RfHTTPBasicOrTokenAuth(HTTPAuth):
    def __init__(self, scheme=None, realm=None):
        super(RfHTTPBasicOrTokenAuth, self).__init__(scheme, realm)
        self.hash_password(None)
        self.verify_basic_password(None)
        self.verify_token(None)

    def hash_password(self, f):
        self.hash_password_callback = f
        return f

    def verify_basic_password(self, f):
        self.verify_password_callback = f
        return f

    def verify_token(self,f):
        self.verify_token_callback = f
        return f
    
    def authenticate_header(self):
        return '{0} realm="{1}"'.format(self.scheme or 'Basic', self.realm)

    def authenticate(self, auth, stored_password, privilege=None):
        if auth:
            username = auth.username
            client_password = auth.password
        else:
            username = ""
            client_password = ""
        if self.verify_password_callback:
            return self.verify_password_callback(username, client_password, privilege=privilege)
        if not auth:
            return False
        if self.hash_password_callback:
            try:
                client_password = self.hash_password_callback(client_password)
            except TypeError:
                client_password = self.hash_password_callback(username,
                                                              client_password)
        return client_password == stored_password

