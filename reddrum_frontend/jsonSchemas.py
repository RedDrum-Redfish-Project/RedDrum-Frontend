
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys
from .redfishUtils import RedfishUtils
from .redfish_headers import RfAddHeaders

class RfJsonSchemas():
    # Note that resource was created in serviceRoot for the session service.
    def __init__(self, rdr):
        self.rdr=rdr
        self.rfutils=RedfishUtils()
        self.loadResourceTemplates()
        self.loadJsonSchemaCollectionResource()
        self.hdrs=RfAddHeaders(rdr)
        self.magic="123456"

    def loadResourceTemplates( self ):
        #load JsonSchemaFile Collection Template
        indxFilePath=os.path.join(self.rdr.baseDataPath,"templates", "JsonSchemaFileCollection.json")
        if os.path.isfile(indxFilePath):
            self.jsonSchemaFileCollectionTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rdr.logMsg("CRITICAL","*****ERROR: JsonSchema Resource: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)

        #load JsonSchemaFile Entry Template
        indxFilePath=os.path.join(self.rdr.baseDataPath,"templates", "JsonSchemaFile.json")
        if os.path.isfile(indxFilePath):
            self.jsonSchemaFileEntryTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rdr.logMsg("CRITICAL","*****ERROR: JsonSchema Resource: Json Data file:{} Does not exist. Exiting".format(indxFilePath))
            sys.exit(10)

    # generate a jsonSchema Database dict with all data needed for Link headers, GET jsonSchema Collection, 
    #   and GET JsonSchema File
    def loadJsonSchemaCollectionResource(self):
        self.jsonSchemasDb=dict()
        dirPath = os.path.join(self.rdr.baseDataPath,"templates")
        for filename in os.listdir(dirPath):
            baseFilename, extension = os.path.splitext(filename)
            if extension == ".json":
                filePath = os.path.join( dirPath, filename)
                templateDict = json.loads( open(filePath, "r").read() )
                rc,namespace, version, resourceType = self.rfutils.parseOdataType(templateDict)
                if(rc == 0):
                    if version is not None:
                        versionedNamespace = namespace + "." + version
                    else:     
                        versionedNamespace = namespace 
                    jsId = versionedNamespace
                    self.jsonSchemasDb[jsId] = {}
                    self.jsonSchemasDb[jsId]["@odata.type"] = templateDict["@odata.type"]
                    self.jsonSchemasDb[jsId]["Namespace"] = namespace
                    self.jsonSchemasDb[jsId]["Version"] = version
                    self.jsonSchemasDb[jsId]["ResourceType"] = resourceType
                    self.jsonSchemasDb[jsId]["VersionedNamespace"] = versionedNamespace
                else:
                    self.rdr.logMsg("ERROR","*****ERROR: JsonSchema Resource: template file:{} missing odata.type.".format(filename))
        return(0)
                    


    # Get JsonSchema Collection
    #  load collection template
    #  for each file in Data/templates, add an entry to the collection Members list
    # Usage:   rc,statusCode,errString,resp,hdr=rdr.root.jsonSchemas.getJsonSchemaCollection(request)
    def getJsonSchemaCollection(self,request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", resource=self.jsonSchemaFileCollectionTemplate, allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        responseData2 = dict(self.jsonSchemaFileCollectionTemplate)
        count=0
        # now walk through the entries in the jsonSchemas and build the chassisCollection Members array
        # note that the members array is an empty array in the template
        uriBase="/redfish/v1/JsonSchemas/"
        for jsonSchemaId in self.jsonSchemasDb:
            # increment members count, and create the member for the next entry
            count=count+1

            memberUri = uriBase + jsonSchemaId
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)


    # Get JsonSchema File
    #  load template
    #  for the filename passed in, 
    #      lookup the odata.type in Data/templates/filename.json,  
    #      then create the response
    #      if rdr.includeLocalJsonSchemas is True, include pointer to the local json schema files
    # Usage:   rc,statusCode,errString,resp,hdr=rdr.root.jsonSchemas.getJsonSchemaFile(jsonSchemaId)
    def getJsonSchemaFile(self, request, jsonSchemaId):
        if jsonSchemaId not in self.jsonSchemasDb:
            return(4, 404, "Not Found", "",{})

        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", resource=self.jsonSchemaFileEntryTemplate, allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # first just copy the template resource
        responseData2=dict(self.jsonSchemaFileEntryTemplate)

        # setup some variables to build response from
        basePath="/redfish/v1/JsonSchemas/"

        # get the specific jsonSchemaId info
        jsInfo = self.jsonSchemasDb[jsonSchemaId]
        if "VersionedNamespace" in jsInfo and "ResourceType" in jsInfo and "Namespace" in jsInfo:
            versionedNamespace = jsInfo["VersionedNamespace"]    # namespace.ver   or namespace (if collection)
            resourceType = jsInfo["ResourceType"]
            namespace = jsInfo["Namespace"]
        else:
            return(5,500,"invalid jsonSchemasDb","",{})

        # assign the required properties
        responseData2["@odata.id"] = basePath + versionedNamespace
        responseData2["Id"] = versionedNamespace
        responseData2["Schema"] = "#" + versionedNamespace + "." + resourceType
        responseData2["Name"] = namespace + " Schema File"
        responseData2["Description"] = jsonSchemaId + " Schema File Location"
        responseData2["Languages@odata.count"] = 1
        responseData2["Location@odata.count"] = 1
        responseData2["Languages"] = ["en"]
        responseData2["Location"] = []

        locationEntry = dict()
        locationEntry["Language"] = "en"
        locationEntry["PublicationUri"] = "http://redfish.dmtf.org/schemas/v1/" + versionedNamespace + ".json"
        if self.rdr.includeLocalJsonSchemas is True:
            locationEntry["Uri"] = "/redfish/v1/schemas/" + versionedNamespace + ".json"
        responseData2["Location"].append( locationEntry ) 

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200,"", jsonRespData2, hdrs)


