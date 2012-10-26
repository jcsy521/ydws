# -*- coding: utf-8 -*-

import re
import logging

from xml.dom import minidom
from constants.LBMP import DUMMY
from codes.errorcode import ErrorCode

class BaseParser(object):

    def __init__(self, message):
        
       self.message = message 
       self.success = ErrorCode.SUCCESS 
       self.info = ErrorCode.ERROR_MESSAGE[ErrorCode.SUCCESS] 
       self.xml = self.__check()

    def __check(self):
   
       if not self.message:
           self.success = ErrorCode.FAILED 
           self.info = ErrorCode.ERROR_MESSAGE[ErrorCode.FAILED] 
           return None
       if self.message == DUMMY:
           self.success = ErrorCode.FAILED 
           self.info = ErrorCode.ERROR_MESSAGE[ErrorCode.FAILED] 
           return None
     
       try:
           xml = minidom.parseString(self.message)
       except Exception as e:
           logging.exception("LBMP: Pase base xml exception:%s", e.args[0])
       else:
           return xml
       return None
