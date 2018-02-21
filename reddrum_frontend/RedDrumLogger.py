
# Copyright Notice:
#    Copyright 2018 Dell, Inc. All rights reserved.
#    License: BSD License.  For full license text see link: https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/LICENSE.txt

# RedDrum Logger Resource -- linux syslog interfaces
#
# Example of how to use logger in other files:
#
#     from RedDrumLogger import Logger
#     logger = Logger()
#     logger.debug("This is a debug level log message")
#     logger.info("This is a info level log message")
#     logger.warn(“This is a warning level log message”')
#     logger.error("This is a error level log message")
#     logger.critical("This is a critical level log message")

import logging
from logging.handlers import SysLogHandler

class RdLogger(object):

     # create logger
     def __init__(self, redDrumServiceName):
          self.serviceName=redDrumServiceName
          self.logger = logging.getLogger(redDrumServiceName)
          self.log_to_syslog()

     # configure the logger to log to syslog
     def log_to_syslog(self):
          formatString = self.serviceName + ': [%(levelname)s] %(message)s'
          formatter = logging.Formatter(formatString)
          handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_DAEMON)
          handler.setFormatter(formatter)
          self.logger.addHandler(handler)
          self.logger.setLevel(logging.DEBUG)
          return(0)

     def rdLoggerMsg(self,sev, *argv, **kwargs):
          if( sev=="INFO"):
               self.logger.info(*argv)
          elif( sev=="WARNING"):
               self.logger.warn(*argv)
          elif( sev=="ERROR"):
               self.logger.error(*argv)
          elif( sev=="CRITICAL"):
               self.logger.critical(*argv)
          else:
               self.logger.debug(*argv)
          return(0)


     # log a debug message
     def debug(self, message):
          self.logger.debug(message)
          return(0)

     # log an info message
     def info(self, message):
          self.logger.info(message)
          return(0)

     # log a waring message
     def warn(self, message):
          self.logger.warn(message)
          return(0)

     # log an error message
     def error(self, message):
          self.logger.error(message)
          return(0)

     # log a critical message
     def critical(self, message):
          self.logger.critical(message)
          return(0)


