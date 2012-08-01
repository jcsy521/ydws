# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE, T_MESSAGE_TYPE

class AsyncRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        if args.command == T_MESSAGE_TYPE.POSITION:
            args.command = S_MESSAGE_TYPE.POSITION
        elif args.command == T_MESSAGE_TYPE.MULTIPVT:
            args.command = S_MESSAGE_TYPE.MULTIPVT
        elif args.command == T_MESSAGE_TYPE.CHARGE:
            args.command = S_MESSAGE_TYPE.CHARGE
        elif args.command == T_MESSAGE_TYPE.ILLEGALMOVE:
            args.command = S_MESSAGE_TYPE.ILLEGALMOVE
        elif args.command == T_MESSAGE_TYPE.POWERLOW:
            args.command = S_MESSAGE_TYPE.POWERLOW
        elif args.command == T_MESSAGE_TYPE.POWEROFF:
            args.command = S_MESSAGE_TYPE.POWEROFF
        elif args.command == T_MESSAGE_TYPE.EMERGENCY:
            args.command = S_MESSAGE_TYPE.EMERGENCY
        else:
            args.command = None
        
        packet = "%s,%s,%s" % (self.time, args['command'], args['success'])
        request = self.format_packet(packet)

        return request 
