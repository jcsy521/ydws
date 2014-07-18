# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class ACCStatusComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S30,0]
        """
        packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.ACC_STATUS,
                               args['success'])
        request = self.format_packet(packet)

        return request

