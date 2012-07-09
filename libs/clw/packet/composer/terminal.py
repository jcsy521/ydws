# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class TerminalComposer(BaseComposer):
 
    def __init__(self, args):
        self.buf = self.compose(args)

    def compose(self, args):
        value = ""
        valid_keys = ['psw', 'domain', 'freq', 'trace', 'pulse', 'phone',
                      'owner_mobile', 'radius', 'vib', 'vibl', 'pof', 'lbv', 
                      'sleep', 'vibgps', 'speed', 'calllock', 'calldisp',
                      'vibcall', 'sms', 'vibchk', 'poft', 'wakeupt', 'sleept',
                      'acclt', 'acclock', 'stop_service', 'cid', 'defend_status',
                      'lock_status']
        for key in args.keys():
            if key.lower() in valid_keys:
                value += "%s=%s" % (key.upper(), args[key])
                if key.lower() == "owner_mobile":
                    value = "%s=%s" % ("USER", args[key])
                break
        packet = ",%s,%s" % (S_MESSAGE_TYPE.TERMINAL, value)
        request = self.format_packet(packet)
        
        return request
