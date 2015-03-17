# -*- coding: utf-8 -*-

"""This module is designed for parameters in platform needed by a terminal.

#NOTE: deprecatd.

"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class TerminalComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        eg: [1343278800,S6,DOMAIN=pinganbb.info:9002,FREQ=15]
        """
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.TERMINAL) 
        params = args['params']
        valid_keys = ['domain', 'freq', 'trace', 'pulse', 'phone',
                      'user', 'vibchk', 'service_status',
                      'white_list', 'vibl']
        for key in params.keys():
            if key.lower() in valid_keys:
                packet += ",%s=%s" % (key.upper(), params[key])
        request = self.format_packet(packet)
        
        return request
