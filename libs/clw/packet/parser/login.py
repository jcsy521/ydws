# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

class LoginParser(object):

    def __init__(self, packet):
        self.ret = self.parse(packet)

    def parse(self, packet):
        terminal_info = DotDict()
        keys = ["t_msisdn", "u_msisdn", "passwd", "imsi", "imei", "factory_name"]
        for i, key in enumerate(keys):
            terminal_info[key] = packet[i]

        return terminal_info
