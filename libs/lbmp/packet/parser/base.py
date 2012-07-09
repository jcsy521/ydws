# -*- coding: utf-8 -*-

import re
import logging

from xml.dom import minidom
from constants.LBMP import DUMMY, ERRORCODE

class BaseParser(object):

    def __init__(self, message):
        
       self.message = re.sub("GB(2312|K)", "UTF-8", message).encode("utf-8", 'ignore')
       self.success = 0
       self.info = ERRORCODE.SUCCESS 
       self.xml = self.__check()

    def __check(self):
   
       if not self.message:
           self.success = -1
           self.info = ERRORCODE.MESSAGE_ERROR
           return None
       if self.message == DUMMY:
           self.success = -1
           self.info = ERRORCODE.SERVER_ERROR
           return None
     
       try:
           xml = minidom.parseString(self.message)
       except Exception as e:
           logging.exception("LBMP: Pase base xml exception:%s", e.args[0])
       else:
           return xml
       return None
