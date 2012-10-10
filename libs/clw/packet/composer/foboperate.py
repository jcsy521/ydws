# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class FobOperateComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S20,ABCDE,0]
        """
        packet = "%s,%s,%s,%s" % (self.time, S_MESSAGE_TYPE.FOBOPERATE,
                                  args['fobid'], args['operate'])
        request = self.format_packet(packet)

        return request
