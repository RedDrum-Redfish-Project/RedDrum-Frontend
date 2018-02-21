
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import sys
import os
import configparser

# global data structure class for RedDrum Redfish Service
class RdRootData():
    def __init__(self):
        # Base Service RedDrum Service properties -passed in as optional commandline args
        self.rdHost="127.0.0.1"
        self.rdPort=5001
        self.isLocal=False
        self.rdServiceName="RedDrumService"
        self.rdTarget="Simulator"        # Simulator, OpenBMC, RackManager, BullRed
        self.rdProfile="BaseServer1"     # used with rdTarget=Simulator to specify the profile 
                                         # valid profiles currently: BaseServer1 | OpenBmc| Dss9000-4nodes
        self.rdVersion="0.9.5"
        self.rdLogger=None
        self.printLogMsgs=False

        # RedDrum.conf  ['Server Section' ] properties
        #   if these are set to None, the default Apache behavior is implemented which  may be no header or Apache generates it

        self.HttpHeaderCacheControl = "no-store"       # controls value returned in header: Cach-Control:
        #  set to:    "no-store"(dflt),  "no-cache",   None(use Apache dflt), "otherVal"(set to value "otherVal")

        self.HttpHeaderServer = None                   # controls value returned in header: Server
        #  set to:    None(use Apache dflt)(the dflt),   "otherVal"(set to value to "otherVal")

        self.HttpHeaderAccessControlAllowOrigin = "*"  # controls value returned in header: Access-Control-Allow-Origin:
        #  set to:    "*"(dflt), "FromOrigin"(set to request hdr "Origin" value), None(use Apache dflt),  or "otherVal"

        self.includeLocalJsonSchemas = True          # include link to local JsonSchema files 
        self.includeLocalRegistries  = True          # include link to local Registries files
        self.useLocalJsonSchemasInLinkHeader = True  # set Link header to point to local jsonSchema URL
                                                     #  only used if includeLocalJsonSchemas is True

        self.processorInfoCacheTimeout = 30          # ProcessorInfoCacheTimeout
        self.simpleStorageInfoCacheTimeout= 30       # SimpleStorageInfoCacheTimeout
        self.ethernetInterfaceInfoCacheTimeout = 30  # EthernetInterfaceInfoCacheTimeout
        self.memoryInfoCacheTimeout = 30             # MemoryInfoCacheTimeout


        # RedDrum.conf  ['Auth Section' ] properties
        self.RedfishAllowAuthNone = False
        self.RedfishAllowAuthenticatedAPIsOverHttp = True
        self.RedfishAllowBasicAuthOverHttp = True
        self.RedfishAllowSessionLoginOverHttp = True
        self.RedfishAllowUserCredUpdateOverHttp = True

        # pointers to backend and root resources
        #   these are initialized by RedDrumMain.py or equivalent
        self.root=None
        self.backend=None

        # RedDrum data paths -- Normally set by Backend root initialization, 
        #    or over-written by setLocalPaths() method below (called by RedDrumMain) if -L / isLocal is set true
        self.baseDataPath=None          # path to the RedDrum Flask Data directory where template and static Json Data is stored
        self.varDataPath=None           # writable dir path where resource caches (including account and session service) data is stored
        self.frontEndDirPath=None       # path to the directory where the Front-end Package is
        self.RedDrumConfPath=None       # path to the RedDrum.conf file
        self.staticConfigDataPath=None  # path to directory where static Config data is retrieved
        #                                  used only if self.resourceDiscovery="Static"
        self.schemasPath=None           # path to local Schema files


        # Other Properties to enable the type of discovery, use of persistent data cache, and static data profiles
        #    self.useCachedDiscoveryDb -- if true resource discovery will start from persistent cache file if it is present
        #    self.resourceDiscovery    -- specifies whether to use "Static" or "Dynamic" discovery
        #                                 "Static" discovery loads resources from a static Json database files 
        #                                 The Simulator config uses Static setting for discovery
        #         
        self.useCachedDiscoveryDb=True        # True or False
        self.useStaticResourceDiscovery=True  # True or False


        # end RedDrum Front-end global rootData
        self.magic=8899


        # Oem flags in FrontEnd
        self.rsaDeepDiscovery=False         # FE-systems


    # log a message. sev= "INFO" "WARNING" "ERROR" "CRITICAL" "DEBUG"
    # if isLocal is true, print the message but dont log
    # if self.printLogMsgs is True, print the message regardless of isLocal
    def logMsg(self, sev, *argv, **kwargs):
        # print to local console if so configured
        if( self.printLogMsgs is True) or (self.isLocal is True):
            print("LOGPRINT: {}:".format(sev),*argv,file=sys.stdout,**kwargs)
            sys.stdout.flush()

        # print to the red drum logger if configured
        # generally, this puts a log msg in syslog with sev= oneOf: "INFO" "WARNING" "ERROR" "CRITICAL" "DEBUG"
        if self.rdLogger is not None:
            self.rdLogger.rdLoggerMsg(sev, *argv, **kwargs)

        return(0)

    # this function sets the paths to the various data files used by the RedDrum service 
    #   for local execution where all of the data is "UNDER" the current working directory
    #   1) varDataPath--path to where the persistent resource cache data data is stored - including roles,...
    #   2) baseDataPath -- path to the "Data" dir where the RedDrum Service code is (for templates)
    #   3) RedDrumConfPath -- path to the RedDrum.conf file to use 
    # these local paths are used generally if isLocal is set to True for developer testing or if running simulator
    #   In RedDrumMain.py, this is called to over-ride whatever paths the Backend put in
    def setLocalPaths(self):
        rdSvcPath=os.getcwd() # get current working dir where the service is being executed from
        if self.frontEndDirPath is None:
            self.frontEndDirPath=rdSvcPath
        self.RedDrumConfPath = os.path.join(rdSvcPath, "RedDrum.conf" ) # use the default flaskapp/RedDrum.conf
        self.varDataPath=os.path.join(rdSvcPath,  "isLocalData", "var", "www", "rf")
        self.baseDataPath=os.path.join(self.frontEndDirPath, "reddrum_frontend", "Data")
        self.schemasPath = os.path.join(rdSvcPath, "schemas")


    # Read the RedDrum.conf file, parse, and store selected properties in the rootData
    def readRedDrumConfFile(self):

        # setting anythong after # as comment
        config = configparser.ConfigParser(inline_comment_prefixes='#')
    
        # First, see if we can read the ConfFIle at the specified path
        if not os.path.isfile(self.RedDrumConfPath):
            self.logMsg("ERROR", "readRedDrumConfFile: Can't read RedDrum.conf file at path {}--continuing w/ defaults".format(self.RedDrumConfPath))
            return(1)

        # read the config file
        try:
            config.read(self.RedDrumConfPath)
        except (IOError, KeyError) as e:
            self.logMsg("ERROR", "readRedDrumConfFile: Error reading RedDrum.conf. ")
            return(2)

        # parse the config file
        rcsum=0
        rc,self.HttpHeaderServer = self.parseConfigProp(config,'Server Section','HttpHeaderServer',"string")
        rcsum+=rc
        rc,self.HttpHeaderCacheControl = self.parseConfigProp(config,'Server Section','HttpHeaderCacheControl',"string")
        rcsum+=rc
        rc,self.HttpHeaderAccessControlAllowOrigin = self.parseConfigProp(config,'Server Section','HttpHeaderAccessControlAllowOrigin',"string") 
        rcsum+=rc

        rc,self.includeLocalJsonSchemas = self.parseConfigProp(config,'Server Section','IncludeLocalJsonSchemaFiles',"boul")
        rcsum+=rc
        rc,self.includeLocalRegistries = self.parseConfigProp(config,'Server Section','IncludeLocalRegistriesFiles',"boul")
        rcsum+=rc
        rc,self.useLocalJsonSchemasInLinkHeader = self.parseConfigProp(config,'Server Section','UseLocalJsonSchemaUrlInLinkHeader',"boul")
        rcsum+=rc

        rc,self.RedfishAllowAuthNone = self.parseConfigProp(config,'Auth Section','RedfishAllowAuthNone',"boul")
        rcsum+=rc
        rc,self.RedfishAllowAuthenticatedAPIsOverHttp = self.parseConfigProp(config,'Auth Section','RedfishAllowAuthenticatedAPIsOverHttp',"boul")
        rcsum+=rc
        rc,self.RedfishAllowBasicAuthOverHttp = self.parseConfigProp(config,'Auth Section','RedfishAllowBasicAuthOverHttp',"boul")
        rcsum+=rc
        rc,self.RedfishAllowSessionLoginOverHttp = self.parseConfigProp(config,'Auth Section','RedfishAllowSessionLoginOverHttp',"boul")
        rcsum+=rc
        rc,self.RedfishAllowUserCredUpdateOverHttp = self.parseConfigProp(config,'Auth Section','RedfishAllowUserCredUpdateOverHttp',"boul")
        rcsum+=rc
        rc,self.processorInfoCacheTimeout = self.parseConfigProp(config,'Server Section','ProcessorInfoCacheTimeout',"int")
        rcsum+=rc
        rc,self.simpleStorageInfoCacheTimeout= self.parseConfigProp(config,'Server Section','SimpleStorageInfoCacheTimeout',"int")
        rcsum+=rc
        rc,self.ethernetInterfaceInfoCacheTimeout = self.parseConfigProp(config,'Server Section','EthernetInterfaceInfoCacheTimeout',"int")
        rcsum+=rc
        rc,self.memoryInfoCacheTimeout = self.parseConfigProp(config,'Server Section','MemoryInfoCacheTimeout',"int")
        rcsum+=rc

        debug = False
        debug = True
        if debug is True:
            print(" DEBUG: rootData Conf file:")
            print("     HttpHeaderServer:                      {}".format( self.HttpHeaderServer ))
            print("     HttpHeaderCacheControl:                {}".format(self.HttpHeaderCacheControl ))
            print("     HttpHeaderAccessControlAllowOrigin:    {}".format( self.HttpHeaderAccessControlAllowOrigin ))

            print("     IncludeLocalJsonSchemaFiles:           {}".format(self.includeLocalJsonSchemas ))
            print("     IncludeLocalRegistriesFiles:           {}".format(self.includeLocalRegistries ))
            print("     UseLocalJsonSchemaUrlInLinkHeader:     {}".format(self.useLocalJsonSchemasInLinkHeader))

            print("     RedfishAllowAuthNone:                  {}".format(self.RedfishAllowAuthNone ))
            print("     RedfishAllowAuthenticatedAPIsOverHttp: {}".format(self.RedfishAllowAuthenticatedAPIsOverHttp ))
            print("     RedfishAllowBasicAuthOverHttp:         {}".format(self.RedfishAllowBasicAuthOverHttp ))
            print("     RedfishAllowSessionLoginOverHttp:      {}".format(self.RedfishAllowSessionLoginOverHttp ))
            print("     RedfishAllowUserCredUpdateOverHttp:    {}".format(self.RedfishAllowUserCredUpdateOverHttp ))

            print("     ProcessorInfoCacheTimeout:             {}".format(self.processorInfoCacheTimeout))
            print("     SimpleStorageInfoCacheTimeout:         {}".format(self.simpleStorageInfoCacheTimeout))
            print("     EthernetInterfaceInfoCacheTimeout:     {}".format(self.ethernetInterfaceInfoCacheTimeout))
            print("     MemoryInfoCacheTimeout:                {}".format(self.memoryInfoCacheTimeout))

        return(rcsum)



    def parseConfigProp(self, config, section, prop, dtype):
        try:
            value = config[section][prop]
        except (IOError, KeyError ) as e:
            self.logMsg("ERROR", "readRedDrumConfFile: Error parsing RedDrum.conf. prop: {}, Error: {}".format( prop, str(e)))
            return(1,None)

        valueLen=len(value)
        #print("EEEEE_rootData_DEGUG: sec:{}, prop:{}, dtype:{}, _value: {}  len(x): {}".format(section,prop,dtype,value,valueLen))
        if dtype=="string":
            if value == "None":
                rdrProp = None
            elif value[0]=='"' and value[valueLen-1]=='"':   # string encapsulated in quotes
                rdrProp = str(value[1:-1])
            elif value[0]=="\'" and value[valueLen-1]=="\'":   # string encapsulated in quotes
                rdrProp = str(value[1:-1])
            else:
                rdrProp = str(value)
        elif dtype=="boul":
            if value == "True" or value=="true":
                rdrProp = True
            elif value == "False" or value=="false":
                rdrProp = False
            else:
                self.logMsg("ERROR", "readRedDrumConfFile: Error parsing RedDrum.conf. prop: {} value not expected boul".format(prop))
                return(1,None)
        elif dtype=="int":
            if value == "None":
                rdrProp = None
            else:
                rdrProp = int(value)
        else:
            self.logMsg("ERROR", "readRedDrumConfFile: Error parsing RedDrum.conf. prop: {} Invalid dtype in rootData.py".format(prop))
            return(1,None)

        return(0,rdrProp)
        
