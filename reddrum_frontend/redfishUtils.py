
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import re
import os

class RedfishUtils():
    def __init__(self):
        #the odataType format is:  <namespace>.[<version>.]<type>   where version may have periods in it 
        self.versionedOdataTypeMatch = re.compile('^#([a-zA-Z0-9]*)\.([a-zA-Z0-9\._]*)\.([a-zA-Z0-9]*)$')
        self.unVersionedOdataTypeMatch = re.compile('^#([a-zA-Z0-9]*)\.([a-zA-Z0-9]*)$')

    # parse the @odata.type property into {namespace, version, resourceType}  following redfish syntax rules
    # returns: rc,namespace, version, resourceType.
    #   if @odata.type is not in resource, returns:   1,None,None,None
    #   if error parsing, odata.type:      returns:   2,None,None,None.
    #   if unversioned collection:         returns:   0,namespace,None,resourceType
    #   if versioned resource:             returns:   0,namespace,version,resourceType
    # usage:   
    #     from .redfishUtils import RedfishUtils
    #     rfutils=RedfishUtils()
    #     rc,namespace, version, resourceType = rfutils.parseOdataType(resource)
    def parseOdataType(self, resource):
        if not "@odata.type" in resource:
            return(1,None,None,None)

        #print("RESOURCE: {}".format(resource)) 
        resourceOdataType=resource["@odata.type"]

        # first try versioned match
        resourceMatch = re.match(self.versionedOdataTypeMatch, resourceOdataType)
        if(resourceMatch is None):
            # try unVersioned match
            resourceMatch = re.match(self.unVersionedOdataTypeMatch, resourceOdataType)
            if( resourceMatch is None):
                return(2,None,None,None)
            else: 
                # unversioned resource eg Collection
                rc=0
                namespace = resourceMatch.group(1)
                version = None
                resourceType = resourceMatch.group(2)
        else:
            # versioned resource 
            rc=0
            namespace = resourceMatch.group(1)
            version = resourceMatch.group(2)
            resourceType = resourceMatch.group(3)

        return(rc, namespace, version, resourceType)


    # return the mimetype/content-type for a schema file based on suffix
    def getContentTypeForFile(self, schemaFile):

        if schemaFile is not None:
            baseFilename, extension = os.path.splitext(schemaFile)
            if extension == "json":
                contentType = "application/json"
            elif extension == "xml":
                contentType = "application/xml"
            else:
                contentType = None
        else:
            contentType = None
        return(contentType)




