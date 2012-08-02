# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict
from codes.clwcode import CLWCode
from constants import EVENTER

class RealtimeParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        if ret.command == 'T4':
            ret['t'] = EVENTER.INFO_TYPE.POSITION
            info = self.get_position(packet)
        else:
            pass

        ret.update(info)

        return ret

    def get_position(self, packet):
        position = {'lon' : 0, 
                    'lat' : 0,
                    'alt' : 0,
                    'cLon' : 0,
                    'cLat' : 0,
                    'name' : None,
                    'valid': 0, 
                    'speed' : 0, 
                    'degree' : 0,
                    'defend_status' : None, 
                    'cellid' : None, 
                    'gps' : None, 
                    'gsm' : None, 
                    'pbat' : None, #volume
                    'gps_time' : None,
                    'dev_type' : None}

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'defend_status', 'cellid', 'extra', 'gps_time']
        for i, key in enumerate(keys):
            position[key] = packet[i]

        keys = ['gps', 'gsm', 'pbat']
        ggp = position['extra'].split(':')
        for i, key in enumerate(keys):
            position[key] = ggp[i]
        del position['extra']

        position['lon'] = int(float(position['lon']) * 3600000)
        position['lat'] = int(float(position['lat']) * 3600000)
        position['speed'] = float(position['speed'])
        position['degree'] = float(position['degree'])
        position['valid'] = self.get_valid(position['valid'])

        return position

    def get_valid(self, valid):
        if valid == '1':
            valid = CLWCode.LOCATION_SUCCESS
        elif valid == '2':
            valid = CLWCode.LOCATION_LAST
        else:
            valid = CLWCode.LOCATION_FAILED

        return valid
