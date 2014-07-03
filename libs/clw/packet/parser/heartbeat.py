# -*- coding: utf-8 -*-

import logging

from utils.dotdict import DotDict
from constants import GATEWAY

class HeartbeatParser(object):
    """Return the structural data for heartbeat(T2)
     
    The instance has ret.

    An example:
    ret:
    {'dev_id': 'CBBJTEAM01', 
     'sleep_status': '0', 
     'softversion': '3.2.ZJ200_1.5113', 
     'dev_type': '3', 
     'timestamp': 1404362326, 
     'fob_status': '0', 
     'sessionID': 'mjp1x2ia', 
     'command': 'T2', 
     'pbat': '28', 
     'gsm': '9', 
     'gps': '24'}  
   
    """

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ['ggp', 'sleep_status', 'fob_status']
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        keys = ['gps', 'gsm', 'pbat']
        ggp = ret['ggp'].split(':')
        for i, key in enumerate(keys):
            ret[key] = ggp[i]
        del ret['ggp']

        return ret
