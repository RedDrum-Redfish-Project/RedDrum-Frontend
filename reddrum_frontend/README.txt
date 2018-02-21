
About:
  This is the Common Flask-based Frontend RedDrum Service.

  It is used as the Frontend Redfish API engine by RedDrum-Simulator and RedDrum-OpenBMC 

  It is also used as the Frontend for the Dell Dss9000 RackManager Redfish Service

Key Interfaces:
  Services that use RedDrum-Frontend as the Redfish API engine must execute a RedDrumMain.py
     progrem (similay ro RedDrum-Frontend/redDrumMain.py) to initializes rootData, create the
     frontend and backend resources, discover actual HW resources, then startup the Flask app.

  The RedDrum-Frontend here provides the APIs for getting rootData, creating the frontend resources,
     and starting the Flask app

  See RedDrum-Frontend/redDrumMain.py for an example Main program to startup

  External APIs used by redDrumMain.py scripts:
     # get the root data including anything read from RedDrum.conf 
     from reddrum_frontend import RdRootData
     rdr=RdRootData().    # RdRootData() is defined in rootData.py.

     # initialize the logger used by the service
     from reddrum_frontend import rdLogger
     rdr.rdLogger=RdLogger(rdr.rdServiceName)

     # create BACKEND resource here---implemented by the implementation specific backend
     # the backend is different for the RedDrum-Simulator and RedDrum-Openbmc implementations
     # RedDrum-Frontend has a dflt backend/ that is just a stub to test the frontend and show flow
     from backend import RedDrumBackend  # the dflt backend stub in RedDrum-Frontend
     rdr.backend=RedDrumBackend(rdr)     # RedDrumBackend is in backendRoot() in the backend dir

     # create the frontend resources
     from reddrum_frontend import RfServiceRoot
     rdr.root=RfServiceRoot(rdr)    # RfServiceRoot() is defined in serviceRoot.py

     # Discover Actual HW Resource that go into the Systems, Managers, and Chassis collections
     # these come from an entry point into the backend
     # RedDrum-Frontend has a dflt backend/ that is just a stub to test the frontend and show flow
     #    here the Chassis, Systems, and Managers collections are empty
     rdr.backend.runStartupDiscovery(rdr)  # adds members to Chassis, Systems, Managers in a real system

     # startup the Flask App which starts the Redfish REST API running in background
     from reddrum_frontend import rdStart_RedDrum_Flask_app
     rdStart_RedDrum_Flask_app(rdr)   # defined in redDrumStartURIs.py


The Flask app must run untreaded because the Frontend updates python dictionary databases as it executes, 
The design is that the frontend must get any updates from the backend quickly so that it does not block
It is the responsibility of the backend design to run multiple threads as necessary and keep telemetry
 data cached if needed.

Redfish Session Auth and Basic Auth is implemented fully in the RedDrum-Frontend underneath Flask.


