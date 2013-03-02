# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser

class GeParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_position(self):
    
       position = dict(clon='',
                       clat='')
       try:
           if self.xml:
               Nodes = self.xml.getElementsByTagName("property")
               for Node in Nodes:
                   if Node.hasAttribute('key') and Node.attributes['key'].value == "china_lng":
                       position['clon'] = int(float(Node.childNodes[0].data) / 1.024)
                   elif Node.hasAttribute('key') and Node.attributes['key'].value == "china_lat":
                       position['clat'] = int(float(Node.childNodes[0].data) / 1.024)
       except Exception as e:
           logging.exception("GE: Parse ge position exception:%s", e.args[0]) 
       return position

    def is_success(self):
        
        if self.xml:
            resultNode = self.xml.getElementsByTagName('result')
            
            if resultNode:
                error_keys = resultNode[0].attributes.keys()
                if "resid" in error_keys:
                    self.success = resultNode[0].attributes['resid'].value
                for node in resultNode[0].childNodes:
                    if node.nodeType == Node.TEXT_NODE:             
                        self.info = node.data
class GdGeParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_position(self):
    
       position = dict(clon='',
                       clat='')
       try:
           if self.xml:
               lonNode = self.xml.getElementsByTagName("x")
               latNode = self.xml.getElementsByTagName("y")
               position['clon'] = lonNode[0].childNodes[0].data
               position['clat'] = latNode[0].childNodes[0].data
       except Exception as e:
           logging.exception("GE: Parse ge position exception:%s", e.args[0]) 
       return position

    def is_success(self):
        
        if self.xml:
            messageNode = self.xml.getElementsByTagName('Message')
            errorcodeNode = self.xml.getElementsByTagName('ErrorCode')
            if messageNode:
                self.info = messageNode[0].childNodes[0].data
            if errorcodeNode:
                self.success = errorcodeNode[0].childNodes[0].data
