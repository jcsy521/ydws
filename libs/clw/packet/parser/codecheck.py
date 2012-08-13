# -*- coding: utf-8 -*-

import time 
import logging

from utils.dotdict import DotDict
from constants.GATEWAY import T_MESSAGE_TYPE

class T_CLWCheck(object):
    """
    report of terminal
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
                head.timestamp = head.timestamp if head.timestamp else int(time.time())
                body = p_info[len(keys):]
            else:
                logging.error("Not a complete packet: %s", packet)
        else:
            logging.error("Invalid packet: %s", packet)
       
        return head, body 
    
class S_CLWCheck(object):
    """
    report of service
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
                head.timestamp = head.timestamp if head.timestamp else int(time.time()) 
                body = p_info[len(keys):]
            else:
                logging.error("Not a complete packet: %s", packet)
        else:
            logging.error("Invalid packet: %s", packet)
       
        return head, body 
