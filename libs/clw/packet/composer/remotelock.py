# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class RemoteLockComposer(BaseComposer):
 
    def __init__(self, args):
        self.buf = self.compose(args['lock_status'])

    def compose(self, lock):
        packet = ",%s,%s" % (S_MESSAGE_TYPE.REMOTELOCK, lock)
        request = self.format_packet(packet)
        
        return request
