
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

from functools import wraps
from flask import request, Response, make_response
from .redfishUtils import RedfishUtils

#
def errorNoHost():
    # return 400-Bad Request
    return Response("", 400)

# Function used to check if header['accept'] contains 'application/xml' or not
# Output : 406-Not Acceptable
def errorNotAcceptable(acceptableValue):
    return Response("",  406, {'Accept': acceptableValue})


# Function used to check if header['content-type'] contains 'charset=utf-8,application/json' or not
# Output : 415-Unsupported Media Type
def errorContentType():
    return Response("" , 415, {'Content-Type': "application/json;charset=utf-8"})

# Function used to check if header['odata-version'] contains '4.0' or not
# Output : 412-Precondition Failed
def errorOdataVersion():
    return Response("", 412, {'OData-Version': '4.0'})


def rfcheckHeaders(*o_args, **o_kwargs):
    
    def header_processor(fn):
        #    Decorator that checks that request headers and validates them accordingly to Redfish Requirements
        #    @app.route("/")
        #    @header_processor
        #    def func():
        #        pass

        @wraps(fn)
        def decorated(*args, **kwargs):
            if "contentType" in o_kwargs:
                contentType=o_kwargs["contentType"]
            else:
                contentType="json"
            #print("EEEEEEEEEEEE: contentType: {}".format(contentType))

            # convert request headers (keys and values) to lower-case for comparisons
            requestHeadersLower = {k.lower() : v.lower() for k,v in request.headers.items()}
            
            # check that the host header was sent:
            if 'host' not in requestHeadersLower:
                return errorNoHost()

            # Checks for rest of URI contains 'application/json' in 'Accept' header or not 
            if contentType=="json":
                acceptable=False
                acceptableAcceptHeaderValuesForJson= ["application/json", "*/*", "application/*"]
                if ('accept' in requestHeadersLower):
                    # note that headers['accept'] may have multiple values like: "application/*;charset=utf-8"
                    for val in acceptableAcceptHeaderValuesForJson:
                        if val in requestHeadersLower["accept"]:
                            acceptable=True
                            break
                    if acceptable is False:
                        return errorNotAcceptable("application/json")

            if contentType=="xml":
                acceptable=False
                acceptableAcceptHeaderValuesForXml = ["application/xml", "*/*", "application/*"]
                if 'accept' in requestHeadersLower:
                    for val in acceptableAcceptHeaderValuesForXml:
                        if val in requestHeadersLower["accept"]:
                            acceptable=True
                            break
                    if acceptable is False:
                        return errorNotAcceptable("application/xml")


            # Checks for methods of PATCH and POST if "Content-Type" in header contains 'charset=utf-8', 'application/json' 
            # or not
            if any(x in request.method for x in ('PATCH', 'POST'))  and ('content-type' in requestHeadersLower):
                if not ( any(x in requestHeadersLower['content-type']  for x in ('charset=utf-8', 'application/json') ) ) :
                    return errorContentType()

            # Checks that if OData-Version if present, the version must be  4.0 or higher
            if ('odata-version' in requestHeadersLower):
                odataVersion = requestHeadersLower['odata-version']
                if(odataVersion !=  '4.0'):
                    return errorOdataVersion()                    

            return (fn(*args, **kwargs))    
        return (decorated)
    return header_processor



class RfAddHeaders():
    def __init__(self, rdr):
        self.rdr = rdr
        self.rfutils = RedfishUtils()

    # creates headers:   
    #    OData-Version, Server, Cache-Control, Access-Control-Allow-Origin -- are returned on all responses
    #           and are driven by settings in rootData / RedDrum.conf
    #    Content-Type -- added if <contentType> is not None. 
    #                    <contentType> is oneOf: None(dflt). "json", "xml", "raw"
    #                    if "json" content-type="application/json;metadata=minimal;charset=utf-8"
    #                    if "xml" content-type="application/xml;charset=utf-8"
    #                    if "raw" content-type="charset=utf-8"
    #    Allow        -- added if <allow> is not None.
    #                    <allow> is oneOf:  None(dflt), "Get"(GET,HEAD), "GetPatch"(GET,HEAD,PATCH), [explicit list]
    #                            where [explicit list] is a list of methods eg ["GET", "PATCH", "HEAD"]
    #    Link         -- added if <resource> is not None.
    #                    <resource> is oneOf:  None(dflt),  <a dict representation of the resource or res template>
    #                            if @odata.type is in <resource>, the Link header is built from odata.type
    #    Location     -- added if <location> is not None.
    #                    <location> is oneOf:  None(dflt),  locationString(the location header value)
    #    X-Auth-Token -- added if <xauthtoken> is not None.
    #                    <xauthtoken> is set to oneOf: None(dflt), tokenString
    #    ETag         -- a Strong Etag is added if <strongEtag> is not None.
    #                      <strongEtag> is oneOf: None(dflt), <etagStringWithoutQuotes>
    #                 -- a Weak Etag is added if <etag> is not None.
    #                       <etag> is oneOf: None(dflt), <etagStringWithoutQuotes>
    #                    If BOTH a strongEtag and etag are sent, the strongEtag will be generated
    def rfRespHeaders(self, request, contentType=None, resource=None, allow=None, location=None, xauthtoken=None, 
                      strongEtag=None, etag=None):
        hdrs=dict()

        # add Odata-Version
        odataVersion=True
        if odataVersion is True:
            hdrs['OData-Version'] = '4.0'

        # add Server header:   supports customizing the Server header based on RedDrum.conf
        if self.rdr.HttpHeaderServer is not None:
            hdrs['Server'] = self.rdr.HttpHeaderServer
        else:
            pass # let Apache fill-in the Server header 


        # add Cache-Control:  indicates if a response can be cached.   
        if self.rdr.HttpHeaderCacheControl is not None:
            hdrs['Cache-Control'] = self.rdr.HttpHeaderCacheControl
        else:
            pass  # use default Apache behavior


        # add Access-Control-Allow-Origin:  return Access Control Allow Origin
        if self.rdr.HttpHeaderAccessControlAllowOrigin is not None:
            if self.rdr.HttpHeaderAccessControlAllowOrigin == "FromOrigin":
                requestHeadersLower = {k.lower() : v for k,v in request.headers.items()}
                if 'origin' in requestHeadersLower:
                    hdrs['Access-Control-Allow-Origin'] = requestHeadersLower['origin']
            else:
                hdrs['Access-Control-Allow-Origin'] = self.rdr.HttpHeaderAccessControlAllowOrigin 
        else:
            pass  # don't create this header--use default Apache behavior 



        # add ContentType
        if contentType is not None:
            if contentType == "json":
                hdrs['Content-Type'] = "application/json;odata.metadata=minimal;charset=utf-8"
            elif contentType == "xml":
                hdrs['Content-Type'] = "application/xml;charset=utf-8"
            elif contentType == "raw":
                hdrs['Content-Type'] = "charset=utf-8"
            else: 
                # if we don't specify anything, then flask will claim it it html. 
                hdrs['Content-Type'] = "charset=utf-8"
        else: 
                # if we don't specify anything, then flask will claim it it html. 
                # and some clients always expect contentType, so we will just return utf8 if there is no response
                # so safest strategy is to return utf8 if there is no response
                hdrs['Content-Type'] = "charset=utf-8"

        # add Allow:   return Allow header from list of Allow headers passed in
        if allow is not None:
            if allow=="Get":
                allowList=["GET","HEAD"]
            elif allow=="GetPatch":
                allowList=["GET","HEAD","PATCH"]
            else:
                allowList=allow
            hdrs['Allow'] = allowList

        # return Link header pointing to the resource
        #  if resourceTemplate is None(the default), don't include the link header
        if resource is not None:
            linkHeader=None
            # parse the odata.type into namespace, version, resourctType.  note that collections don't have a version
            rc,namespace,version,resourceType = self.rfutils.parseOdataType(resource)
            if rc==0:
                if version is None:
                    versionedNamespace = namespace + ".json"
                else:
                    versionedNamespace = namespace + "." + version + ".json"

                if (self.rdr.includeLocalJsonSchemas is True) and (self.rdr.useLocalJsonSchemasInLinkHeader is True):
                    # set Link header to point to local jsonSchema uri
                    linkHeader= "</redfish/v1/schemas/" + versionedNamespace + ">;rel=describedby"
                else:
                    # set Link header to point to dmtf hosted jsonSchema uri
                    linkHeader= "<http://redfish.dmtf.org/schemas/v1/" + versionedNamespace + ">;rel=describedby"
            else:
                # there was no @odata.type in the resource, so don't add a Link header
                #   this will be the case for odata, metadata, redDrumInfo, etc
                pass

            if linkHeader is not None:
                hdrs['Link'] = linkHeader

        # add location
        if location is not None:
            hdrs['Location'] = location

        # add x-auth-token
        if xauthtoken is not None:
            hdrs['X-Auth-Token'] = xauthtoken

        # add strong etag.   strong etags contain a hashString enclosed by quotes
        if strongEtag is not None:
            hdrs['ETag'] = '"' + strongEtag + '"'

        elif etag is not None:
            # add strong etag.   strong etags contain a hashString enclosed by quotes
            hdrs['ETag'] = 'W/"' + etag + '"'

        # return the hdrs dict back
        return(hdrs)


