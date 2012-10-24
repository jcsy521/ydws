# -*- coding: utf-8 -*-

import logging
import base64

from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY

class AsyncParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        info = {}

        if ret.command  == 'T3':
            ret['t'] = EVENTER.INFO_TYPE.POSITION
            ret['Tid'] = self.get_tid(ret.command) 
            info = self.get_position_info(packet)
        elif ret.command  == 'T11': # pvt
            ret['t'] = EVENTER.INFO_TYPE.POSITION
            ret['Tid'] = self.get_tid(ret.command)
            info = self.get_pvt_info(packet)
        elif ret.command in ('T13', 'T14', 'T15', 'T16'):
            ret['t'] = EVENTER.INFO_TYPE.REPORT
            ret['rName'] = self.get_tid(ret.command) 
            info = self.get_report_info(packet)
        elif ret.command == 'T12':
            ret['t'] = EVENTER.INFO_TYPE.CHARGE
            info = self.get_charge_info(packet)
        elif ret.command == 'T18':
            info = self.get_defend_info(packet)
        elif ret.command == 'T21':
            info = self.get_sleep_info(packet)
        elif ret.command == 'T22':
            info = self.get_fob_info(packet)
        else:
            return info 

        info.update(ret)

        return info

    def get_tid(self, command):
        if command == "T3":
            tid = EVENTER.TRIGGERID.CALL
        elif command == "T11":
            tid = EVENTER.TRIGGERID.PVT
        elif command == "T13":
            tid = EVENTER.RNAME.ILLEGALMOVE
        elif command == "T14":
            tid = EVENTER.RNAME.POWERLOW
        elif command == "T15":
            tid = EVENTER.RNAME.ILLEGALSHAKE
        elif command == "T16":
            tid = EVENTER.RNAME.EMERGENCY
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
                    'defend_status' : None, 
                    'cellid' : None, 
                    'gps' : None, 
                    'gsm' : None, 
                    'pbat' : None, #volume
                    'gps_time' : None,
                    'dev_type' : None}

        return position 

    def get_charge_info(self, packet):
        content = base64.decodestring(packet[0]).decode('utf-8')
        info = {'content': content}

        return info

    def get_defend_info(self, packet):
        defend_status = packet[0]
        info = {'defend_status': defend_status}

        return info

    def get_sleep_info(self, packet):
        sleep_status = packet[0]
        info = {'sleep_status': sleep_status}

        return info

    def get_fob_info(self, packet):
        fob_status = packet[0]
        info = {'fob_status': fob_status}

        return info

    def get_pvt_info(self, packet):
        positions = []
        keys = ['ew', 'lon', 'ns', 'lat', 'speed', 'degree', 'gps_time'] 
        for index in range(len(packet)/len(keys)):
            position = self.get_position()
            pvt = packet[index*len(keys):index*len(keys)+len(keys)]
            for i, item in enumerate(pvt):
                item = item.replace('{', '')
                item = item.replace('}', '')
                position['t'] = EVENTER.INFO_TYPE.POSITION 
                position[keys[i]] = item 
            position['lon'] = int(float(position['lon']) * 3600000)
            position['lat'] = int(float(position['lat']) * 3600000)
            position['speed'] = float(position['speed'])
            position['degree'] = float(position['degree'])
            position['gps_time'] = int(position['gps_time'])
            position['valid'] = GATEWAY.LOCATION_STATUS.UNREALTIME
            positions.append(position)
        info = {'pvts': positions}

        return info 

    def get_position_info(self, packet):
        """Extrac position info from the async report.
           CALL

        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'defend_status', 'cellid', 'extra', 'gps_time']
        position = self.get_position()
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
        position['gps_time'] = int(position['gps_time'])

        return position 

    def get_report_info(self, packet):
        """Get the location report information. Location is classified as the 
        following categories: ILLEGALSHAKE, POWERLOW, EMERGENCY, ILLEGALMOVE 
        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed', 'degree',
                'defend_status', 'cellid', 'extra', 'gps_time', 'terminal_type',
                'fobid']
        position = self.get_position()
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
        position['gps_time'] = int(position['gps_time'])

        return position 

