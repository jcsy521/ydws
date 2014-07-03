# -*- coding: utf-8 -*-

import time 
import logging

from utils.dotdict import DotDict
from constants.GATEWAY import T_MESSAGE_TYPE

class T_CLWCheck(object):
    """ Report of terminal.
     
    Returns head, body
    
    An example. 
    head:
    {'dev_id': '18701638494', 
     'softversion': '3.3.1', 
     'dev_type': '1', 
     'timestamp': 1404364119, 
     'sessionID': '', 
     'command': 'T1'}

    body:
    ['18701638494', 
     '13011292217', 
     '18701638494', 
     '', 
     'CLW', 
     '2', 
     '0', 
     'bt_mac', 
     'bt_name']
    """
    def __init__(self, packet):
        self.head, self.body = self.parse_head(packet)

    def parse_head(self, packet):
        head = DotDict()
        body = []
        if packet.startswith('[') and packet.endswith(']'):
            p_info = packet[1:-1].split(',')
            keys = ['timestamp', 'sessionID', 'dev_type', 'softversion', 'dev_id', 'command']
            if len(p_info) >= len(keys):
                for i, key in enumerate(keys):
                    head[key] = p_info[i]
                head.timestamp = int(head.timestamp) if head.timestamp else int(time.time())
                body = p_info[len(keys):]
            else:
                logging.error("Not a complete packet: %s", packet)
        else:
            logging.error("Invalid packet: %s", packet)
       
        return head, body 
    
class S_CLWCheck(object):
    """Report of service.
    """
    def __init__(self, packet):
        self.head, self.body = self.parse_head(packet)

    def parse_head(self, packet):
        head = DotDict()
        body = []
        if packet.startswith('[') and packet.endswith(']'):
            p_info = packet[1:-1].split(',') 
            keys = ['timestamp', 'command']
            if len(p_info) >= len(keys):
                for i, key in enumerate(keys):
                    head[key] = p_info[i]
                head.timestamp = int(head.timestamp) if head.timestamp else int(time.time()) 
                body = p_info[len(keys):]
            else:
                logging.error("Not a complete packet: %s", packet)
        else:
            logging.error("Invalid packet: %s", packet)
       
        return head, body 
