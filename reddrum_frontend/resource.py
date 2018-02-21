
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import os
import json
import sys
from .redfish_headers import RfAddHeaders

# RfStaticResource( rfr, flag, filePath, dataFile, contentType="json")
#    flag= string to indicate where to get initial data (baseData or varData, etc)
#        "var" or "base" are defined
#    filePath= path from the base data to the file.   usually "static".  Dont include a leading /, it can be empty ""
#    dataFile= the file to load
#    contentType = "json"(the default) or "xml" or "raw"
#         if contentType="json", the json file is loaded into a dict.   Otherwise the file contents are stored raw

class RfStaticResource():
    def __init__(self, rfr, flag, filePath, dataFile, contentType="json"):
        self.contentType = contentType
        if( flag == "base" ):
            indxFilePath=os.path.join(rfr.baseDataPath,filePath, dataFile)
        elif( flag == "var" ):
            indxFilePath=os.path.join(rfr.varDataPath, filePath, dataFile)
        else:
            rfr.logMsg("CRITICAL","****resource.py: Internal error, invalid flag given to init method: {}. Exiting".format(flag))
            sys.exit(9)

        if os.path.isfile(indxFilePath):
            # load data into dict
            if( self.contentType=="json"):
                self.resData=json.loads( open(indxFilePath,"r").read() )
            else:
                self.resData=( open(indxFilePath,"r").read())
        else:
            rfr.logMsg("CRITICAL","****resource.py: Json Data file:{} Does not exist. Exiting.".format(indxFilePath))
            sys.exit(10)

        self.createSubObjects(rfr, flag)
        self.finalInitProcessing(rfr, flag)
        self.magic="123456"

    def createSubObjects(self, rfr, flag):
        pass

    def finalInitProcessing(self, rfr, flag):
        self.hdrs=RfAddHeaders(rfr)

    def getResource(self,request):
        hdrs = self.hdrs.rfRespHeaders(request,contentType=self.contentType,resource=self.resData,allow="Get")
        if request.method=="HEAD":
            return(0,200,"","",hdrs)
        if self.contentType=="json":
            response=json.dumps(self.resData,indent=4)
        else:
            response=self.resData
        return(0,200,"",response,hdrs)




