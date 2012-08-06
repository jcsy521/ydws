# -*- coding:utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode

from clw.packet.composer.query import QueryComposer
from clw.packet.parser.query import QueryParser

from gf.packet.composer.sendcomposer import SendComposer
from gf.packet.parser.sendparser import SendParser

from base import BaseHandler

class QueryHandler(BaseHandler):

    @tornado.web.asynchronous
    def do_post(self, args):
        """
        workflow:
        vg_buf = VGComposer(args)
        gf_buf = GFComposer(vg_buf, args)
        get vg_buf via QueryComposer(), then get complete gf_buf
        via SendComposer(), send it!
        """
        
        logging.debug("query terminal attribute post args:%s", args) 

        qc = QueryComposer(args)
        sc = SendComposer(qc.buf, args)

        logging.debug("query terminal attribute post request:\n%r", sc.buf) 

        def _on_finish(response):    
            """
            @params: response 
                     {success='xx', 
                      info='xx',
                      vgdata='xx'}
            @return: ret, write it to uweb          
            """
            try:
                logging.debug("query terminal attribute post response:\n%r", response)
                ret = dict(success=response.success,
                           info=response.info)
                if response.clwhead and response.clwbody:
                    rp = QueryParser(response.clwbody, response.clwhead)
                    ret['params'] = rp.ret['params']

                self.set_header(*self.JSON_HEADER)
                self.write(json_encode(ret))
                self.finish()
            except Exception as e:
                # NOTE: async timeout
                logging.exception("Request terminal set error: %s", e.args)

        request = dict(packet=sc.buf, callback=_on_finish)
        self.sender.send_queue.put(request)
