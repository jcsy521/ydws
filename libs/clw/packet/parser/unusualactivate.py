# -*- coding: utf-8 -*-


class UnusualActivateParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ["t_msisdn", "u_msisdn", "imsi"]
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret 


