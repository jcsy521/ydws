# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class QueryComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        #valid_keys = ['SOFTVERSION', 'GSM', 'GPS', 'VBAT', 'VIN', 'LOGIN',
        #              'PLCID', 'IMSI', 'IMEI']
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.QUERY)
        for key in args['params']:
            packet += ",%s" % key.upper()
        request = self.format_packet(packet)
        
        return request
