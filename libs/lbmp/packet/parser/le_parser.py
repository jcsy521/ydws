# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser

class LeParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_position(self):
    
       position = dict(lon='',
                       lat='')
       try:
           if self.xml:
               LonNodes = self.xml.getElementsByTagName("X")
               LatNodes = self.xml.getElementsByTagName("Y")
               for node in (LonNodes, LatNodes):
                   if node[0].nodeName == "Y" and node[0].childNodes[0].nodeType == Node.TEXT_NODE:
                       position['lon'] = node[0].childNodes[0].data
                   elif node[0].nodeName == "X" and node[0].childNodes[0].nodeType == Node.TEXT_NODE:
                       position['lat'] = node[0].childNodes[0].data
       except Exception as e:
           logging.exception("LE: Parse le position exception:%s", e.args[0]) 
       return position

    def is_success(self):
        
        if self.xml:
            resultNode = self.xml.getElementsByTagName('result')
            errorinfoNode = self.xml.getElementsByTagName('add_info')
            
            if resultNode:
                error_keys = resultNode[0].attributes.keys()
                if "resid" in error_keys:
                    self.success = resultNode[0].attributes['resid'].value
            if errorinfoNode:
                for node in errorinfoNode[0].childNodes:
                    if node.nodeType == Node.TEXT_NODE:
                        self.info = node.data
