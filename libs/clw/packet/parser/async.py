# -*- coding: utf-8 -*-

import logging
import base64

from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY

class AsyncParser(object):
    """Parser to get the whole packets, which forward to eventer.
    """

    def __init__(self, body, head):
        """

        :arg body: list
        :arg head: dict

        :return position: dict 
        """ 
        self.ret = self.parse(body, head)

    def parse(self, body, head):
        info = {}

        if head.command  == 'T3': # position
            head['t'] = EVENTER.INFO_TYPE.POSITION
            head['Tid'] = self.get_tid(head.command) 
            info = self.get_position_info(body)
        elif head.command  == 'T11': # pvt
            head['t'] = EVENTER.INFO_TYPE.POSITION
            head['Tid'] = self.get_tid(head.command)
            info = self.get_pvt_info(body)
        elif head.command in ('T13', 'T14', 'T15', 'T16', 'T26', 'T29'):
            # various reports
            head['t'] = EVENTER.INFO_TYPE.REPORT
            head['rName'] = self.get_tid(head.command) 
            info = self.get_report_info(body)
        elif head.command == 'T12': # charge #NOTE: deprecated
            head['t'] = EVENTER.INFO_TYPE.CHARGE
            info = self.get_charge_info(body)
        elif head.command == 'T18':
            info = self.get_defend_info(body)
        elif head.command == 'T21':
            info = self.get_sleep_info(body)
        elif head.command == 'T22':
            info = self.get_fob_info(body)
        elif head.command == 'T23':
            info = self.get_runtime_info(body)
        elif head.command == 'T25':
            info = self.get_unbind_info(body) 
        else:
            return info 

        info.update(head)

        return info

    def get_tid(self, command):
        """Get the tid according the command(Tx)

        e.g:
        T3-->CALL
        T11-->PVT
        """
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

        :return position: dict
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

    def get_charge_info(self, body):
        """Get the charge information. T12

        #NOTE: deprecated

        :arg body: list
        :return position: dict 
        """  

        content = base64.decodestring(body[0]).decode('utf-8')
        info = {'content': content}

        return info

    def get_defend_info(self, body):
        """Get the defend information. T18

        :arg body: list
        :return position: dict 
        """  
        defend_status = body[0]
        defend_source = body[1]
        info = {'defend_status': defend_status,
                'defend_source': defend_source}

        return info

    def get_sleep_info(self, body):
        """Get the sleep information. T21

        :arg body: list
        :return position: dict 
        """  
        sleep_status = body[0]
        info = {'sleep_status': sleep_status}

        return info

    def get_fob_info(self, body):
        """Get the fob information. T22

        :arg body: list
        :return position: dict 
        """        
        fob_status = body[0]
        info = {'fob_status': fob_status}

        return info

    def get_runtime_info(self, body):
        """Get the runtime information. T23

        :arg body: list
        :return position: dict 
        """
        runtime_info = {} 
        runtime_info['login'] = body[0]
        runtime_info['defend_status'] = body[1]
        runtime_status = body[2]
        runtime_info['fob_pbat'] = body[3] if body[3] else '-1'
        runtime_info['is_send'] = body[4] if body[4] else '0'
        keys = ['gps', 'gsm', 'pbat']
        ggp = runtime_status.split(':')
        for i, key in enumerate(keys):
            runtime_info[key] = ggp[i]
        return runtime_info

    def get_unbind_info(self, body):
        """Get the unbind information.
        #NOTE: deprecated

        :arg body: list
        :return position: dict 
        """
        flag = body[0] 
        info = {'flag':flag}

        return info

    def get_pvt_info(self, body):
        """Get the pvt information. T11

        :arg body: list
        :return position: dict 
        """
        #NOTE: reorganize the body. if locate_error is missed, add a default value
        starts_index = []
        ends_index = []
        for index, p in enumerate(body): 
            if p.startswith('{'): 
                starts_index.append(index) 
            if p.endswith('}'): 
                ends_index.append(index)
        group_index = zip(starts_index, ends_index)
        body_new = []
        for start_index, end_index in group_index: 
            pvt = body[start_index:end_index+1] 
            if len(pvt) == 7: 
                pvt[-1] = pvt[-1][:-1] 
                pvt.append('20') 
                pvt.append('}') 
                logging.info("[GW] old version is compatible, append locate_error, misc")
            elif len(pvt) == 8: 
                pvt[-1] = pvt[-1][:-1] 
                pvt.append('}') 
                logging.info("[GW] old version is compatible, append misc")
            body_new.extend(pvt) 

        positions = []

        # 9 items
        keys = ['ew', 'lon', 'ns', 'lat', 'speed', 'degree', 'gps_time', 'locate_error', 'misc'] 

        for index in range(len(body_new)/len(keys)):
            start_index = index*len(keys)
            end_index = index*len(keys)+len(keys)
            position = self.get_position()
            pvt = body_new[start_index:end_index]

            for i, item in enumerate(pvt):
                #NOTE: just remove {} in body
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

    def get_position_info(self, body):
        """Extrac position info from the async report.
           CALL

        :arg body: list
        :return position: dict 
        """

        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed',
                'degree', 'defend_status', 'cellid', 'extra', 'gps_time',
                'locate_error']

        #NOTE: if some new fields was added, provide a default value        
        keys_miss = len(keys) - len(body)
        for i in range(keys_miss):
            body.append('')

        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = body[i]


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

    def get_report_info(self, body):
        """Get the location report information. Location is classified as the 
        following categories: 
        ILLEGALSHAKE, POWERLOW, EMERGENCY, ILLEGALMOVE 

        :arg body: list
        :return position: dict 
        """
        # 15 itesm.
        keys = ['valid', 'ew', 'lon', 'ns', 'lat', 'speed', 'degree',
                'defend_status', 'cellid', 'extra', 'gps_time', 'terminal_type',
                'fobid', 'locate_error', 'is_notify']

        #NOTE: If the body misses some field, provide a '' 
        keys_miss = len(keys) - len(body)
        logging.info("[GW] body: %s, keys_miss: %s", body, keys_miss)
        for i in range(keys_miss):
            body.append('')


        #NOTE: unpack extra into gps, gsm, pbat 
        position = self.get_position()
        for i, key in enumerate(keys):
            position[key] = body[i] 

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
