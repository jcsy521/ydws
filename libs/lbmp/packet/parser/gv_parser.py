# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser

class GvParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_location(self):
    
       location = dict(name='')
       try:
           if self.xml:
               Nodes = self.xml.getElementsByTagName("freeFormAddress")
               for Node in Nodes:
                   location['name'] = Node.childNodes[0].data
       except Exception as e:
           logging.exception("GV: Parse location exception:%s", e.args[0]) 
       return location

    def is_success(self):
        
        if self.xml:
            errorNodes = self.xml.getElementsByTagName('Error')
            ServiceError = self.xml.getElementsByTagName('ServiceError')
            XMLError = self.xml.getElementsByTagName('XMLError')
            InfoNodes = ServiceError if ServiceError else XMLError
            
            if errorNodes:
                self.success = -1

            if InfoNodes:
                if "message" in InfoNodes[0].attributes.keys():
                    self.info = InfoNodes[0].attributes['message'].value
