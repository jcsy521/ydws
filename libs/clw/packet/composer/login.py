# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class LoginRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        type = S_MESSAGE_TYPE.LOGIN 
        success = args['success']
        info = args['info']
        packet = ','.join([self.time, type, success, info])
        return self.format_packet(packet)
