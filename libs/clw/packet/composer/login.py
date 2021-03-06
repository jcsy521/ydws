# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class LoginRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        
        eg: [1343278800,S1,0,1q2w3e45]
        """
        command = S_MESSAGE_TYPE.LOGIN 
        success = args['success']
        sessionID = args['sessionID']
        packet = ','.join([self.time, command, success, sessionID])
        request = self.format_packet(packet)

        return request 
