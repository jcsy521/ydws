# -*- coding: utf-8 -*-

class ACCStatusParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        """
        parameters of T30:
        1. parameters
        2. source, 0: fob, 1: platform 
        3. timestamp

        """
        keys = ["acc_status", "acc_source", "timestamp"]
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret 

