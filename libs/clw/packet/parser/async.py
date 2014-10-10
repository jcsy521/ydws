# -*- coding: utf-8 -*-

import logging
import base64

from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY

class AsyncParser(object):
    """Parser packets which forward to eventer.
    """

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
        elif ret.command in ('T13', 'T14', 'T15', 'T16', 'T26', 'T29'):
            #report
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
        elif ret.command == 'T23':
            info = self.get_runtime_info(packet)
        elif ret.command == 'T25':
            info = self.get_unbind_info(packet) 
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
        elif command == "T26":
            tid = EVENTER.RNAME.POWERDOWN
        elif command == "T29":
            tid = EVENTER.RNAME.STOP
        else:
            tid = None

        return tid

    def get_position(self):
        """Provide a default dict.
        """
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
        defend_source = packet[1]
        info = {'defend_status': defend_status,
                'defend_source': defend_source}

        return info

    def get_sleep_info(self, packet):
        sleep_status = packet[0]
        info = {'sleep_status': sleep_status}

        return info

    def get_fob_info(self, packet):
        fob_status = packet[0]
        info = {'fob_status': fob_status}

        return info

    def get_runtime_info(self, packet):
        runtime_info = {} 
        runtime_info['login'] = packet[0]
        runtime_info['defend_status'] = packet[1]
        runtime_status = packet[2]
        runtime_info['fob_pbat'] = packet[3] if packet[3] else '-1'
        runtime_info['is_send'] = packet[4] if packet[4] else '0'
        keys = ['gps', 'gsm', 'pbat']
        ggp = runtime_status.split(':')
        for i, key in enumerate(keys):
            runtime_info[key] = ggp[i]
        return runtime_info

    def get_unbind_info(self, packet):
        flag = packet[0] 
        info = {'flag':flag}

        return info

    def get_pvt_info(self, packet):

        #NOTE: reorganize the packet. if locate_error is missed, add a default value
        starts_index = []
        ends_index = []
        for index, p in enumerate(packet): 
            if p.startswith('{'): 
                starts_index.append(index) 
            if p.endswith('}'): 
                ends_index.append(index)
        group_index = zip(starts_index, ends_index)
        packet_new = []
        for start_index, end_index in group_index: 
            pvt = packet[start_index:end_index+1] 
            if len(pvt) == 7: 
                pvt[-1] = pvt[-1][:-1] 
                pvt.append('20') 
                pvt.append('}') 
                logging.info("[GW] old version is compatible, append locate_error, misc")
            elif len(pvt) == 8: 
                pvt[-1] = pvt[-1][:-1] 
                pvt.append('}') 
                logging.info("[GW] old version is compatible, append misc")
            packet_new.extend(pvt) 

        positions = []

        # 9 items
        keys = ['ew', 'lon', 'ns', 'lat', 'speed', 'degree', 'gps_time', 'locate_error', 'misc'] 

        for index in range(len(packet_new)/len(keys)):
            start_index = index*len(keys)
            end_index = index*len(keys)+len(keys)
            position = self.get_position()
            pvt = packet_new[start_index:end_index]

            for i, item in enumerate(pvt):
                #NOTE: just remove {} in packet
                item = item.replace('{', '')
                item = item.replace('}', '')
                position['t'] = EVENTER.INFO_TYPE.POSITION 
                position[keys[i]] = item 

            #NOTE: some format-deal for body
            position['lon'] = int(float(position['lon']) * 3600000)
            position['lat'] = int(float(position['lat']) * 3600000)
            position['speed'] = float(position['speed'])
            position['degree'] = float(position['degree'])
            position['gps_time'] = int(position['gps_time'])
            position['valid'] = GATEWAY.LOCATION_STATUS.SUCCESS 

            if not position.get('locate_error', None):
                position['locate_error'] = 20 # default value 20
            position['locate_error'] = int(position['locate_error']) 
            if not position.get('misc', None):
                position['misc'] = '' # default value ''
            positions.append(position)

        info = {'pvts': positions}

        return info 

    def get_position_info(self, packet):
        """Extrac position info from the async report.
           CALL

        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'defend_status', 'cellid', 'extra', 'gps_time',
                'locate_error']

        #NOTE: if some new fields was added, provide a default value        
        keys_miss = len(keys) - len(packet)
        for i in range(keys_miss):
            packet.append('')

        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = packet[i]


        keys = ['gps', 'gsm', 'pbat']
        ggp = position['extra'].split(':')
        for i, key in enumerate(keys):
            position[key] = ggp[i]
        del position['extra']

        #NOTE: some format-deal for body
        position['lon'] = int(float(position['lon']) * 3600000)
        position['lat'] = int(float(position['lat']) * 3600000)
        position['speed'] = float(position['speed'])
        position['degree'] = float(position['degree'])
        position['gps_time'] = int(position['gps_time'])

        if not position.get('locate_error', None):
            position['locate_error'] = 20 # default value 
        position['locate_error'] = int(position['locate_error']) 

        return position 

    def get_report_info(self, packet):
        """Get the location report information. Location is classified as the 
        following categories: ILLEGALSHAKE, POWERLOW, EMERGENCY, ILLEGALMOVE 
 
        """
        # 15 itesm.
        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed', 'degree',
                'defend_status', 'cellid', 'extra', 'gps_time', 'terminal_type',
                'fobid', 'locate_error', 'is_notify']

        #NOTE: If the packet misses some field, provide a '' 
        keys_miss = len(keys) - len(packet)
        logging.info("[GW] packet: %s, keys_miss: %s", packet, keys_miss)
        for i in range(keys_miss):
            packet.append('')


        #NOTE: unpack extra into gps, gsm, pbat 
        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = packet[i] 

        #NOTE: unpack extra into gps, gsm, pbat 
        keys = ['gps', 'gsm', 'pbat']
        ggp = position['extra'].split(':')
        for i, key in enumerate(keys):
            position[key] = ggp[i]
        del position['extra']
   
        #NOTE: some format-deal for body
        position['lon'] = int(float(position['lon']) * 3600000)
        position['lat'] = int(float(position['lat']) * 3600000)
        position['speed'] = float(position['speed'])
        position['degree'] = float(position['degree'])
        position['gps_time'] = int(position['gps_time'])

        #NOTE: IF locate_error is inexistence, provide 20 default 
        if not position.get('locate_error', None):
            position['locate_error'] = 20 # default value 
        position['locate_error'] = int(position['locate_error']) 

        return position 
