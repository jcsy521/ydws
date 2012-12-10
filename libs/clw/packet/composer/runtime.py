# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class RuntimeRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S23,0,1]
        """
        packet = "%s,%s,%s,%s" % (self.time, S_MESSAGE_TYPE.RUNTIMESTATUS, args['success'], args['mannual_status'])
        request = self.format_packet(packet)

        return request
