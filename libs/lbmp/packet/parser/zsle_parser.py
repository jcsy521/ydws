# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser
from utils.dotdict import DotDict

class ZsLeParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_position(self):
    
       position = DotDict(lon='',
                          lat='')
       try:
           if self.xml:
               LonNodes = self.xml.getElementsByTagName("coordX")
               LatNodes = self.xml.getElementsByTagName("coordY")
               for node in (LonNodes, LatNodes):
                   if node[0].nodeName == "coordX" and node[0].childNodes[0].nodeType == Node.TEXT_NODE:
                       position['lon'] = float(node[0].childNodes[0].data) * 3600000
                   elif node[0].nodeName == "coordY" and node[0].childNodes[0].nodeType == Node.TEXT_NODE:
                       position['lat'] = float(node[0].childNodes[0].data) * 3600000
       except:
           logging.exception("[LBMP] Parse le position exception.") 
       return position

    def is_success(self):
        if self.xml:
            try:
                resultNode = self.xml.getElementsByTagName('result')
                errMsgNode = self.xml.getElementsByTagName('errMsg')
            
                if resultNode and resultNode[0].childNodes[0].nodeType == Node.TEXT_NODE:
                    result = resultNode[0].childNodes[0].data
                    self.success = result

                if errMsgNode and len(errMsgNode[0].childNodes) > 0:
                    if errMsgNode[0].childNodes[0].nodeType == Node.TEXT_NODE:
                        errMsg = errMsgNode[0].childNodes[0].data
                        self.info = errMsg
            except:
                logging.exception("[LBMP] Parse le success exception.")
