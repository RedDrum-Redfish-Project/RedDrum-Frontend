
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

# OEM-specific ID construction and interpretation utilities
# NOTE:
#  in Redfish, it is generally not safe for a client to construct of assume construction of a URI
#  However, the RedDrum fronend interprets some IDs loaded during discovery for some response construction.
#  These OEM utilities contain any special rules re interpreting IDs 

import re

class Dell_Dss9000_OemUtils():
    def __init__(self):
        self.isBlockRe=re.compile("^Rack[1-9][0-9]{0,3}-Block([1-9]|10)$")
        self.isPowerBayRe=re.compile("^Rack[1-9][0-9]{0,3}-PowerBay[1-4]$")

    def rsdLocation(self, chassid):
        rack,chas,sled=self.getChassisSubIds(chassid)
        #print("rack: {}, chas: {}, sled: {}".format(rack,chas,sled))
        if chas is None:
            id=rack
            parent=None
        elif sled is None:
            id=chas
            parent=rack
        else:
            id=sled
            parent=chas
        return( id, parent)

    def isBlock(self,chassid):
        if re.search(self.isBlockRe, chassid) is not None:
            return True
        else:
            return False

    def isPowerBay(self,chassid):
        if ( re.search(self.isPowerBayRe, chassid)) is not None:
            return True
        else:
            return False
