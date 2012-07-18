# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict
from constants import EVENTER
from codes.clwcode import CLWCode

class AsyncParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        info = {}

        if ret.type == 'T3':
            ret['t'] = EVENTER.INFO_TYPE.POSITION
            ret['Tid'] = self.get_tid(ret.type) 
            info = self.get_position_info(packet)
        elif ret.type in ('T11', 'T12', 'T14', 'T15'):
            ret['t'] = EVENTER.INFO_TYPE.REPORT
            ret['rName'] = self.get_tid(ret.type) 
            info = self.get_report_info(packet)
        elif ret.type == 'T13':
            ret['t'] = EVENTER.INFO_TYPE.REPORT
            ret['rName'] = self.get_tid(ret.type) 
            info = self.get_power(packet)
        elif ret.type == 'T16':
            ret['t'] = EVENTER.INFO_TYPE.STATISTICS
            ret['statistics'] = EVENTER.STATISTICS.MILEAGE
            info = self.get_mileage(packet)
        else:
            return info 

        info.update(ret)

        return info

    def get_tid(self, type):
        if type == "T3":
            tid = EVENTER.TRIGGERID.CALL
        elif type == "T11":
            tid = EVENTER.RNAME.ILLEGALMOVE
        elif type == "T12":
            tid = EVENTER.RNAME.POWEROFF
        elif type == "T13":
            tid = EVENTER.RNAME.POWERLOW
        elif type == "T14":
            tid = EVENTER.RNAME.REGION_OUT
        elif type == "T15":
            tid = EVENTER.RNAME.SPEED_OUT
        else:
            tid = None

        return tid

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
                    'status' : 0, 
                    'cellid' : None, 
                    'gps' : 0, 
                    'gsm' : 0, 
                    'volume' : 0}
        return position 

    def get_valid(self, valid):
        if valid == '1':
            valid = CLWCode.LOCATION_SUCCESS
        elif valid == '2':
            valid = CLWCode.LOCATION_LAST
        else:
            valid = CLWCode.LOCATION_FAILED

        return valid

    def get_position_info(self, packet):
        """Extrac position info from the async report.
           CALL

        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'status', 'cellid']
        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = packet[i]

        keys = ['gps', 'gsm', 'volume']
        for i, key in enumerate(keys):
            position[key] = str(packet[-1:][0])[i]

        position['lon'] = int(float(position['lon']) * 3600000)
        position['lat'] = int(float(position['lat']) * 3600000)
        position['speed'] = float(position['speed'])
        position['degree'] = float(position['degree'])

        #NOTE: here, just stor 0, 3, 6, 9 in database to show the electry quantity of battery 
        #d = {'0' : 3.65,
        #     '3' : 3.7,
        #     '6' : 4.15,
        #     '9' : 4.2}
        #volume = position['volume']
        #if volume in d:
        #    position['volume'] = d[volume]
        #else:
        #    position['volume'] = 0

        position['valid'] = self.get_valid(position['valid']) 

        return position 

    def get_report_info(self, packet):
        """Get the location report information. Location is classified as the 
        following categories: REGION_ENTER, REGION_OUT, POWERON, POWEROFF
        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'status', 'cellid']
        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = packet[i] 

        position['lon'] = int(float(position['lon']) * 3600000)
        position['lat'] = int(float(position['lat']) * 3600000)
        position['speed'] = float(position['speed'])
        position['degree'] = float(position['degree'])
        position['valid'] = self.get_valid(position['valid']) 

        return position 

    def get_power(self, packet):
        position = self.get_position()
        position['volume'] = int(packet[0])/1000.0
        position['valid'] = self.get_valid(position['valid']) 

        return position 

    def get_mileage(self, packet):
        info = DotDict(mileage=packet[0])

        return info

