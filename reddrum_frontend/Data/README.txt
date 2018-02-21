
These json database files are used by the RedDrum-Frontend to create responses and to initialize 
the accountService and sessionService databases:

Directories: /templates, /static, /registries  -- are used by the Frontend to construct proper responses.
      and should not be modifies w/o a good understand of how the code uses the data

Directory: /db contains the default configuration for the AccountService and SessionService
   These can be edited for an implementation if different default values are desired.
   Redfish APIs can also be used to update these.

   When the Frontend starts, if there is no current cache for these files exists (eg under /var/...) , 
     the serviceRoot will create a cache from these files.   If the caches exist, it continues to use them.

   --/db/AccountsDb.json -- contains four default users: root, redfish_adm, redfish_oper,  redfish_readonly
     passwords are root:passowrd, redfish_adm:password_adm, redfish_oper:password_oper, redfish_readonly:password_readonly
     the root user can not be deleted

   --/db/RolesDb.json --  the predefined Redfish Roles:  Administrator, Operator, ReadOnly

   --/db/AccountServiceDb.json -- default AccountService properties

   --/db/SessionServiceDb.json -- default SessionService properties
