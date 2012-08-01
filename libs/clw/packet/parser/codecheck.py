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
        self.packets_info = self.parse_head(packet)

    def parse_head(self, packets):
        packets_info = []
        if packets.startswith('[') and packets.endswith(']'):
            packet_list = packets[1:-1].split('][')
            for packet in packet_list:
                packet_info = DotDict(head=DotDict(), body="")
                p_info = packet.split(',') 
                keys = ['timestamp', 'sessionID', 'dev_type', 'version', 'dev_id', 'command']
                for i, key in enumerate(keys):
                    packet_info.head[key] = p_info[i]
                timestamp = packet_info.head.timestamp if packet_info.head.timestamp else int(time.time())
                packet_info.body = p_info[len(keys):]
                packet_info.message = "[" + packet + "]"
                packets_info.append(packet_info)
        else:
            logging.warn("[GW] Invalid packets:%s", packets)
       
        return packets_info 
    
class S_CLWCheck(object):
    """
    report of service
    """
    def __init__(self, packet):
        self.head, self.body = self.parse_head(packet)

    def parse_head(self, packet):
        packet = packet[1:-1].split(',') 
        head = DotDict()
        keys = ['timestamp', 'command']
        for i, key in enumerate(keys):
            head[key] = packet[i]
        timestamp = head.timestamp if head.timestamp else time.strftime("%Y-%m-%d %H:%M:%S")
        head.timestamp = int(time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))) * 1000
       
        return head, packet[len(keys):]
