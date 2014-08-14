# -*- coding: utf-8 -*-

class ACCStatusReportParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        """
        parameters of T31:
        1. 0: GSensor; 1: ACC 

        """
        keys = ["category"]
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret 

