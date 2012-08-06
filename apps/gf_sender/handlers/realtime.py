# -*- coding:utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode

from clw.packet.composer.realtime import RealtimeComposer
from clw.packet.parser.realtime import RealtimeParser

from gf.packet.composer.sendcomposer import SendComposer
from gf.packet.parser.sendparser import SendParser

from base import BaseHandler

class RealtimeHandler(BaseHandler):

    @tornado.web.asynchronous
    def do_post(self, args):
        """
        workflow:
        clw_buf = CLWComposer(args)
        gf_buf = GFComposer(clw_buf, args)
        get clw_buf via RealtimeComposer(), then get complete gf_buf
        via SendComposer(), send it!
        """
        
        logging.debug("realtime post args:%s", args) 

        rc = RealtimeComposer()
        sc = SendComposer(rc.buf, args)

        logging.debug("realtime post request:\n%r", sc.buf) 

        def _on_finish(response):    
            """
            @params: response 
                     {success='xx', 
                      info='xx',
                      clwhead={},
                      clwbody='xx'}
            @return: ret, write it to uweb          
            """
            try:
                logging.debug("realtime post response:\n%r", response)
                ret = dict(success=response.success,
                           info=response.info,
                           position={})
                if response.clwhead and response.clwbody:
                    rp = RealtimeParser(response.clwbody, response.clwhead)
                    ret['position'] = rp.ret

                self.set_header(*self.JSON_HEADER)
                self.write(json_encode(ret))
                self.finish()
            except Exception as e:
                # NOTE: async timeout
                logging.exception("Request realtime error: %s", e.args)

        request = dict(packet=sc.buf, callback=_on_finish)
        self.sender.send_queue.put(request)
