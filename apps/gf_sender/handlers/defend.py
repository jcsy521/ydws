# -*- coding:utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from codes.clwcode import CLWCode

from clw.packet.composer.defend import DefendComposer
from clw.packet.parser.defend import DefendParser

from gf.packet.composer.sendcomposer import SendComposer
from gf.packet.parser.sendparser import SendParser

from base import BaseHandler

class DefendHandler(BaseHandler):

    @tornado.web.asynchronous
    def do_post(self, args):
        """
        workflow:
        clw_buf = CLWComposer(args)
        gf_buf = GFComposer(clw_buf, args)
        get clw_buf via DefendComposer(), then get complete gf_buf
        via SendComposer(), send it!
        """
        
        logging.debug("defend post args:%s", args) 

        dc = DefendComposer(args)
        sc = SendComposer(dc.buf, args)

        logging.debug("defend post request:\n%r", sc.buf) 

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
                logging.debug("defend post response:\n%r", response)
                ret = dict(success=response.success,
                           info=response.info)
                if response.clwhead and response.clwbody:
                    rp = DefendParser(response.clwbody, response.clwhead)
                    status = rp.ret['status']
                    if status == GATEWAY.DEFEND_STATUS.SUCCESS : 
                        ret['success'] = ErrorCode.SUCCESS
                    else:
                        ret['success'] = ErrorCode.FAILED

                self.set_header(*self.JSON_HEADER)
                self.write(json_encode(ret))
                self.finish()
            except Exception as e:
                # NOTE: async timeout
                logging.exception("Request defend error: %s", e.args)

        request = dict(packet=sc.buf, callback=_on_finish)
        self.sender.send_queue.put(request)
