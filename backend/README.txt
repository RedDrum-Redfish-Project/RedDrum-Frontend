
This directory contains a stub Backend sufficient for the RedDrum-Frontend Service to run for testing the front-end.
   This is useful for testing services that are fully contained in the Frontend:

Note that Back-ends are generally "implementation-specific" and contain the code that the RedDrum-Frontend uses
   to get platform-specific data about resources.  This includes discovery and monitoring APIs.

   This backend is a "stub" just for testing the common Frontend service including:
   -- AccountServie and all authentication, accounts APIs, and Role APIs
   -- SessionService 
   -- RootSerivce
   -- and major collection APIs including Systems, Managers, Chassis

The real Backend for the RedDrum Simulator   is in the Repo:  RedDrum-Redfish-Project/RedDrum-Simulator.
The real Backend for the RedDrum OpenBMC     is in the Repo:  RedDrum-Redfish-Project/RedDrum-OpenBMC.
The real Backend for the RedDrum RackManager is in the Repo:  RedDrum-Redfish-Project/RedDrum-RackManager.


