#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom import minidom
import logging

class SMSParser(object):
    
    
    def __init__(self, packet):
        self.response_code = '-1'
        self.response_text = None
        try:
            xml = minidom.parseString(packet.encode('utf-8'))
            self.response_code = xml.getElementsByTagName("c")[0].childNodes[0].data
            self.response_text = xml.getElementsByTagName("d")[0].childNodes[0].data
        except Exception as e:
            logging.exception("Parse response packet error, packet : %s", packet)
        
        
