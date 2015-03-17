# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

class LoginParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        # keys = ["t_msisdn", "u_msisdn", "imsi", "imei", "factory_name",
        #         "keys_num", "psd", "bt_name", "bt_mac"]
        parm = dict(t_msisdn=packet[0],
        	       u_msisdn=packet[1],
        	       imsi=packet[2],
        	       imei=packet[3],
        	       factory_name=packet[4],
        	       keys_num=packet[5],
        	       psd=packet[6],
        	       bt_name=packet[7],
        	       bt_mac=packet[8])
        ret.update(parm)

        # for i, key in enumerate(keys):
        #     ret[key] = packet[i]

        return ret 
