
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys
from .redfishUtils import RedfishUtils
from .redfish_headers  import RfAddHeaders

class RfRegistries():
    def __init__(self,rdr):
        self.rdr=rdr
        self.rfutils=RedfishUtils()
        self.loadResourceTemplates()
        self.loadRegistriesCollectionResource()
        self.hdrs=RfAddHeaders(rdr)
        self.magic="123456"

    def loadResourceTemplates( self ):
        #load Registries Collection Template
        indxFilePath=os.path.join(self.rdr.baseDataPath,"templates", "MessageRegistryFileCollection.json")
        if os.path.isfile(indxFilePath):
            self.registryFileCollectionTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rdr.logMsg("CRITICAL","*****ERROR: Registries Resource: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)

        #load Registries Entry Template
        indxFilePath=os.path.join(self.rdr.baseDataPath,"templates", "MessageRegistryFile.json")
        if os.path.isfile(indxFilePath):
            self.registryFileEntryTemplate=json.loads( open(indxFilePath,"r").read() )
        else:
            self.rdr.logMsg("CRITICAL","*****ERROR: Registries Resource: Json Data file:{} Does not exist. Exiting".format(indxFilePath))
            sys.exit(10)


    # generate a Registries Database dict with all data needed for Link headers, GET Registries Collection, and GET Registry File
    def loadRegistriesCollectionResource(self):
        self.registriesDb=dict()
        dirPath = os.path.join(self.rdr.baseDataPath,"registries")
        for filename in os.listdir(dirPath):
            registryError = False
            baseFilename, extension = os.path.splitext(filename)
            if extension == ".json":
                filePath = os.path.join( dirPath, filename)
                templateDict = json.loads( open(filePath, "r").read() )
                #rc,namespace, version, resourceType = self.rfutils.parseOdataType(templateDict)
                requiredProperties = ["RegistryPrefix","RegistryVersion","Name","Description"]
                for prop in requiredProperties:
                    if prop not in templateDict:
                        self.rdr.logMsg("ERROR","*****ERROR: Registry file: {} missing required property: {}.".format(filename,prop))
                        registryError = True
                if registryError is True:
                    continue  # go on to next registry file

                regPrefix  = templateDict["RegistryPrefix"]
                regVersion = templateDict["RegistryVersion"]
                regId = regPrefix + "." + regVersion
                self.registriesDb[regId] = {}
                self.registriesDb[regId]["RegistryVersion"] = regVersion
                self.registriesDb[regId]["RegistryPrefix"] =  regPrefix
                self.registriesDb[regId]["Name"] = templateDict["Name"]
                self.registriesDb[regId]["Description"] = templateDict["Description"]
                self.registriesDb[regId]["Registry"] = templateDict["Registry"]
        return(0)


    # GET Registries Collection
    #  load collection template
    #  for each file in Data/templates, add an entry to the collection Members list
    # Usage:   rc,statusCode,errString,resp,hdr=rdr.root.registries.getRegistriesCollection(request)
    def getRegistriesCollection(self,request):
        hdrs=self.hdrs.rfRespHeaders(request, contentType="json", resource=self.registryFileCollectionTemplate, allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        responseData2 = dict(self.registryFileCollectionTemplate)
        count=0
        # now walk through the entries in the jsonSchemas and build the chassisCollection Members array
        # note that the members array is an empty array in the template
        uriBase="/redfish/v1/Registries/"
        for regId in self.registriesDb:
            # increment members count, and create the member for the next entry
            count=count+1

            memberUri = uriBase + regId
            newMember=[{"@odata.id": memberUri}]

            # add the new member to the members array we are building
            responseData2["Members"] = responseData2["Members"] + newMember

        # update the members count
        responseData2["Members@odata.count"]=count

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200, "", jsonRespData2, hdrs)





    # GET Registries File
    # Usage:   rc,statusCode,errString,resp,hdr=rdr.root.registries.getRegistriesFile(registryId)
    def getRegistriesFile(self, request, registryId):
        if registryId not in self.registriesDb:
            return(4, 404, "Not Found", "",{})

        hdrs = self.hdrs.rfRespHeaders(request, contentType="json", resource=self.registryFileEntryTemplate, allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)

        # first just copy the template resource
        responseData2=dict(self.registryFileEntryTemplate)

        # setup some variables to build response 
        basePath="/redfish/v1/Registries/"

        # get the specific jsonSchemaId info
        regInfo = self.registriesDb[registryId]

        regInfoProps = ["RegistryPrefix","RegistryVersion","Name","Description","Registry"]
        for prop in regInfoProps: 
            if prop not in regInfo:
                return(5,500,"invalid registryDb entry","",{})
        regId = regInfo["RegistryPrefix"] + "." + regInfo["RegistryVersion"]

        # assign the required properties
        responseData2["@odata.id"] = basePath + regId
        responseData2["Id"] = regId
        responseData2["Registry"] = regInfo["Registry"]
        responseData2["Name"] = regInfo["Name"]
        responseData2["Description"] = regInfo["Description"]
        responseData2["Languages@odata.count"] = 1
        responseData2["Location@odata.count"] = 1
        responseData2["Languages"] = ["en"]
        responseData2["Location"] = []

        locationEntry = dict()
        locationEntry["Language"] = "en"
        locationEntry["PublicationUri"] = "http://redfish.dmtf.org/schemas/registries/v1/" + regId + ".json"
        if self.rdr.includeLocalRegistries is True:
            locationEntry["Uri"] = "/redfish/v1/schemas/registries/" + regId + ".json"
        responseData2["Location"].append( locationEntry )

        # convert to json
        jsonRespData2=(json.dumps(responseData2,indent=4))

        return(0, 200,"", jsonRespData2, hdrs)


