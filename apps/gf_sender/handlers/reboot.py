# -*- coding:utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode

from clw.packet.composer.reboot import RebootComposer
from clw.packet.parser.reboot import RebootParser

from gf.packet.composer.sendcomposer import SendComposer
from gf.packet.parser.sendparser import SendParser

from base import BaseHandler

class RebootHandler(BaseHandler):

    @tornado.web.asynchronous
    def do_post(self, args):
        """
        workflow:
        vg_buf = VGComposer(args)
        gf_buf = GFComposer(vg_buf, args)
        get vg_buf via ConfigComposer(), then get complete gf_buf
        via SendComposer(), send it!
        """
        
        logging.debug("reboot post args:%s", args) 

        rc = RebootComposer(args)
        sc = SendComposer(rc.buf, args)

        logging.debug("reboot post request:\n%r", sc.buf) 

        def _on_finish(response):    
            """
            @params: response 
                     {success='xx', 
                      info='xx',
                      clwhead={},
                      clwdata='xx'}
            @return: ret, write it to uweb          
            """
            try:
                logging.debug("reboot post response:\n%r", response)
                ret = dict(success=response.success,
                           info=response.info)
                if response.clwhead and response.clwbody:
                    rp = RebootParser(response.clwbody, response.clwhead)
                    if int(rp.ret['status']) == CLWCode.SUCCESS:
                        ret['success'] = ErrorCode.SUCCESS
                    else:
                        ret['success'] = ErrorCode.FAILED
                        ret['info'] = None

                self.set_header(*self.JSON_HEADER)
                self.write(json_encode(ret))
                self.finish()
            except Exception as e:
                # NOTE: async timeout
                logging.exception("Request reboot error: %s", e.args)
        request = dict(packet=sc.buf, callback=_on_finish)
        self.sender.send_queue.put(request)
