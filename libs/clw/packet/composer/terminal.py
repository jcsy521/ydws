# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class TerminalComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.TERMINAL) 
        params = args['params']
        valid_keys = ['psw', 'domain', 'freq', 'trace', 'pulse', 'phone',
                      'owner_mobile', 'radius', 'vib', 'vibl', 'pof', 'lbv', 
                      'sleep', 'vibgps', 'speed', 'calllock', 'calldisp',
                      'vibcall', 'sms', 'vibchk', 'poft', 'wakeupt', 'sleept',
                      'acclt', 'acclock', 'stop_service', 'cid', 'defend_status',
                      'lock_status']
        for key in params.keys():
            if key.lower() in valid_keys:
                packet += ",%s=%s" % (key.upper(), params[key])
        request = self.format_packet(packet)
        
        return request
