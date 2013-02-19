# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class ConfigRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S17,0,DOMAIN=www.pinganbb.info:8002,AGPS_SERVER=www.pinganbb.info:9002]
        """
        packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.CONFIG,
                               args['success']) 
        for key in ['domain', 'freq', 'trace']:
            packet += ",%s=%s" % (key.upper(), args[key])
        request = self.format_packet(packet)
        
        return request
