
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

import string
import random
def  rfGenerateId(leading="",size=8):
    chars=string.ascii_uppercase+string.digits
    respp=''.join(random.choice(chars) for _ in range(size))
    respp=leading+respp
    return(respp)
