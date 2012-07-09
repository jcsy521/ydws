#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

class BaseParser(object):

    def __init__(self, packet):
        self.packet = packet 
        self.packet_info = self.get_packet_info()

    def get_packet_info(self):
        packet_info = [] 
        try:
            packet = self.is_valid()
            packet_info = packet.split(",")
            self.type = packet_info[1]
        except:
            logging.exception("[GW] Base parse exception.") 
        return packet_info
        
    
    def is_valid(self):
        return self.packet[1:][:-1]
