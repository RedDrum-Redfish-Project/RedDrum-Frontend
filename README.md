# RedDrum Frontend  
The common Frontend App for RedDrum Redfish Servers

## About ***RedDrum-Frontend***

***RedDrum-Frontend*** is a python app (based on Flask) that implements the frontend Redfish API protocol, authentication,
ServiceRoot, AccountSerivce, SessionSerivce, and APIs for JsonSchemas, Registries, and Metadata.

***RedDrum-Frontend*** is used as the "Frontend" Redfish API service for other ***RedDrum*** Redfish Service Implementations:
*  **RedDrum-Simulator** -- a 'high fidelity' Redfish simulator supporting authentication, HTTPS, and several (growing) system hardware configurations
*  **RedDrum-OpenBMC** -- a python based Redfish service integrated with the OpenBMC
*  **RedDrum-Aggregator** -- (uses RedDrum-Frontend v2.x.x) a Redfish service that aggregates several Redfish services (eg several BMCs) and provides a single consolidated Redfish Serivce such as to management of a rack of servers

***RedDrum-Frontend*** attempts to be implementation-independent, and relies on implementation-***specific*** code
in the ***Backend*** of RedDrum Redfish implementations to implement Hardware resource discovery and access actual
hardware sensors.  

RedDrum-OpenBMC and RedDrum-Simulator, [and RedDrum-Aggregator]  each have implementation-specific Backends.

During ***Resource Discovery***, the Backend ***Discovery*** code loads data into the Frontend python dictionary databases.
(for v1.x.x of the Frontend, all data is cached in frontend databases--this changes for v2.x.x)

After discovery, the v1.x.x Frontend code calls various resource ***update*** methods implemented in the Backends to update
Implementation-specific Systems, Chassis, and Managers resources.
Actions (e.g system reset) are also implemented with implementation-specific Backend methods called by the Frontend.

Using the common ***RedDrum-Frontend*** makes it easier to develop the different implementation-specific Redfish Servers 
since this common Frontend code handles of the Redfish protocol details and common Redfish services of the Redfish API.
The implementation-specific Backend code only has to focus on how to discover the hardware resources, get sensor readings,
and implement actions.

## About the ***RedDrum Redfish Project***
The ***RedDrum Redfish Project*** includes several github repos for implementing python Redfish servers.
* RedDrum-Frontend  -- the Redfish Service Frontend that implements the Redfish protocol and common service APIs
* RedDrum-Httpd-Configs -- docs and setup scripts to integrate RedDrum with common httpd servers eg Apache and NGNX
* RedDrum-Simulator -- a "high-fidelity" simulator built on RedDrum with several feature profiles and server configs
* RedDrum-OpenBMC -- a RedDrum Redfish service integrated with the OpenBMC platform
* RedDrum-Aggregator -- a RedDrum Redfish service that aggregates several 2nd level Redfish services such as for a Rack Level Service

## RedDrum Redfish Service Architecture Architecture httpd, frontend, backend
RedDrum Redfish Service Architecture breaks the Redfish service into three parts:
* A standard httpd service 
  * The httpd service implements a virtual server for both http(port 80) and https(port 443) and handles all 
  * any incoming http[s] API with URI starting with `/redfish` is "reverse proxied" to the RedDrum-Frontend using http
  * the Frontend by default listens on http:<127.0.0.1:5001> and only uses Redfish URIs starting with `/redfish`.
  * so SSL is handled by the httpd 
  * this architecture allows other http services to use the same standard http ports
  * SEE RedDrum-Redfish-Project/RedDrum-Httpd-Config  Repo for description of how to configure the various httpd's

* The RedDrum-Frontend -- implementation independent frontend code contained in RedDrum-Frontend
  * All Authentication and Authorization is implemented by the Frontend
  * ServiceRoot, SessionService, AccountService are fully implemented by Frontend
  * valid URI paths are matched against supported methods and the appropriate frontend routines to execute
  * request headers and verified, and response headers generated
  * For Chassis, Systems, and Managers data, responses are generated based on the data in the frontend database for that resource.  The Backend updates the data in the database 
  * the frontend is single threaded but blazing fast since much of the data is cached in the frontend dictionaries

* The RedDrum-Backend -- implements implementation-depended interfaces to the real hardware resources

## Conformance Testing
One of the benefits of leveraging the RedDrum frontend and RedDrum implementations is that the code has been and is actively
being tested against DMTF/SPMF Conformance tools.  

RedDrum has previously passed all of the DMTF Conformance test tools and as new versions of tools are released or updates to
RedDrum are made, additional testing will be made. 
* list of DMTF/SPMF Conformance tools tested against include:
  * Mockup-Creator
  * Service-Validator
  * JsonSchema-Response-Validator
  * Conformance-Check

* RedDrum-specific tests (not yet open sourced)
  * RedDrum-URI-Tester -- tests against all supported URIs for specific simulator profiles
  * RedDrum-Stress-Tester -- runs 1000s of simultaneous requests in parallel


---
## How to Install
#### Install from a Cloned Repo
* An easy way to install the RedDrum-Frontend during development is to clone the repo and then include the repo directory in the python path of the code that is using it

```
    # clone the repo
    cd <directory-above-where-you-want-the-cloned-repo>
    git clone -b v1.0.0 --single-branch https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend  
       # this will get all of the code, data files, documentation, tools, and README.txts for version v1.0.0

    # put the "reddrum_frontend" package from RedDrum-Frontend clone directory into site packages in the python path
    # case1: to install in non-editable mode (where you cant edit the Frontend code for development):
    pip install ./RedDrum-Frontend

    # case2:  to install in "editible mode" where any changes you make to the Frontend Repo will show up in the site pkg
    pip install -e ./RedDrum-Frontend

    # and to uninstall, simply run:
    pip uninstall reddrum_frontend
```

#### Install using `pip install` from the RedDrum-Frontend github github repo
* This gets the latest version of Frontend on github and installs it into your local site-packages
* The package name is `reddrum_frontend`
  * Code that wants to use the Frontend, can simply run: `from reddrum_frontend import <api>`
  * See the redDrumMain.py for example of how to use the Frontend APIs to start a Redfish Service
  * Also see documentation of the Frontend APIs used by redDrumMain.py in  RedDrum-Frontend/reddrum_frontend/README.txt 

```
    # install from github using pip install
    pip install https://github.com/RedDrum-Redfish-Project/archive/v1.0.0.tar.gz 

```

#### Install using `pip install` from pypi (not working yet)
* ***RedDrum-Frontend is not yet registered with pypi***
* Once That is done:
  * This will gets the latest version of Frontend on github and installs it into your local site-packages
    * Code that wants to use the Frontend, can simply run: `from reddrum_frontend import <api>`
    * See the redDrumMain.py for example of how to use the Frontend APIs to start a Redfish Service
    * Also see documentation of the Frontend APIs used by redDrumMain.py in  RedDrum-Frontend/reddrum_frontend/README.txt 
    * you can run the following commands and it will install RedDrum-Frontend to your site-packages
  * The package name is `reddrum_frontend`

```
    # install from pypi using pip install
     pip install RedDrum-Frontend==v1.0.0
```


### How to Start a Redfish Service Using reddrum_frontend from RedDrum-Frontend
* See RedDrum-Frontend/reddrum_frontent/README.txt for details re the APIs that the Main Start script uses
* Or look at the redDrumSimulatorMain.py script in RedDrum-Simulator or RedDrum-OpenBMC as an example
  * the redDrumMain.py in RedDrum-Frontend is used to test frontend services w/ a stubbed out backend
  * you can look at it if you clone the Frontend repo--it doesn't install from pip
* More detail docs on How to Use coming...
---
