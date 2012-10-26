# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser

class SubscriptionParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def is_success(self):
        if self.xml:
            try:
                resultIdNode = self.xml.getElementsByTagName('resultId')
                resultInfoNode = self.xml.getElementsByTagName('resultInfo')
                            
                if resultIdNode and resultIdNode[0].childNodes[0].nodeType == Node.TEXT_NODE:
                    resultId = resultIdNode[0].childNodes[0].data
                    self.success = resultId
                        
                if resultInfoNode and resultInfoNode[0].childNodes[0].nodeType == Node.TEXT_NODE:
                    resultInfo = resultInfoNode[0].childNodes[0].data
                    self.info = resultInfo
            except:
                logging.exception("[LBMP] Parse subscription xml exception.")
