# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class HeartbeatRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        
        eg: [1343278800,S2,0,0,1405650165]

        """
        if len(args) == 1:
            packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.HEARTBEAT,
                                   args['success'])
        else:
            packet = "%s,%s,%s,%s,%s" % (self.time, S_MESSAGE_TYPE.HEARTBEAT,
                                         args['success'],
                                         args.get('op_type',''),
                                         args.get('timestamp',''))
        request = self.format_packet(packet)

        return request
