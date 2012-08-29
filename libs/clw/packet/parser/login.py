# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

class LoginParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ["t_msisdn", "u_msisdn", "imsi", "imei", "factory_name",
                "keys_num", "psd"]
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret 
