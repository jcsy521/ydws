# -*- coding: utf-8 -*-

import time 
import logging

from utils.dotdict import DotDict
from constants.GATEWAY import T_MESSAGE_TYPE

class T_CLWCheck(object):
    """Packet come from terminal. It's map to the packet from terminal(Tx).

    It's has two parameters:
    1. head
    2. body
    
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
        self.head, self.body = self.__parse(packet)

    def __parse(self, packet):
        """Parse the head part of the packet. 

        :arg packet: str
        :return head: dict 
        :return body: list
        """
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
                logging.error("[CLWPARSE] Not a complete packet: %s", packet)
        else:
            logging.error("[CLWPARSE] Invalid packet: %s", packet)
       
        return head, body 
    
class S_CLWCheck(object):
    """Packet send to terminal. It's map to the packet from platform(Sx).
    """
    def __init__(self, packet):
        self.head, self.body = self.__parse(packet)

    def __parse(self, packet):
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
                logging.error("[CLWPARSE] Not a complete packet: %s", packet)
        else:
            logging.error("[CLWPARSE] Invalid packet: %s", packet)

        return head, body 
