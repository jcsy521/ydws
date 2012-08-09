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
        valid_packets = []

        while len(packets) > 0:
            start_index = packets.find('[')
            end_index = packets.find(']')
            if start_index == -1 or end_index == -1:
                logging.error("[GW] Invalid packets:%s", packets)
                packets = ''
            elif end_index < start_index:
                logging.error("[GW] Invalid packets:%s", packets[:start_index])
                packets = packets[start_index:]
            else:
                packet = packets[start_index:end_index+1]
                tmp_index = packet[1:].rfind('[')
                if tmp_index != -1:
                    logging.error("[GW] Invalid packets:%s", packets[:tmp_index])
                    packet = packet[tmp_index:]
                valid_packets.append(packet)
                packets = packets[end_index+1:]

        for packet in valid_packets:
            packet_info = DotDict(head=DotDict(), body="")
            p_info = packet[1:-1].split(',')
            keys = ['timestamp', 'sessionID', 'dev_type', 'softversion', 'dev_id', 'command']
            if len(p_info) > len(keys):
                for i, key in enumerate(keys):
                    packet_info.head[key] = p_info[i]
                timestamp = packet_info.head.timestamp if packet_info.head.timestamp else int(time.time())
                packet_info.body = p_info[len(keys):]
                packet_info.message = packet
                packets_info.append(packet_info)
            else:
                logging.error("[GW] Not full packets:%s", packet)
       
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
        timestamp = head.timestamp if head.timestamp else int(time.time()) 
       
        return head, packet[len(keys):]
