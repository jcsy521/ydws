# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class LocationDescRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        
        eg: [1343278800,S10,0,xxx,E,xx,N,yy]
        """
        packet = "%s,%s,%s,%s,%s,%s,%s,%s" % (self.time, S_MESSAGE_TYPE.LOCATIONDESC, 
                                              args['success'],
                                              args['locationdesc'],
                                              args['ew'],
                                              args['lon'],
                                              args['ns'],
                                              args['lat'])
        request = self.format_packet(packet)

        return request
