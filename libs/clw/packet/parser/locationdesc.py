# -*- coding: utf-8 -*-

import logging

class LocationDescParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def get_position(self):
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

        return position 

    def parse(self, packet, ret):
        position = self.get_position()
        ret.update(position)
        keys = ['ew', 'lon', 'ns', 'lat', 'cellid', 'valid', 'locate_error'] 
        for i, key in enumerate(keys):
            ret[key] = packet[i]
        ret['lon'] = int(float(ret['lon']) * 3600000)
        ret['lat'] = int(float(ret['lat']) * 3600000)
        ret['gps_time'] = int(ret['timestamp'])
        ret['locate_error'] = int(ret['locate_error'])

        return ret

