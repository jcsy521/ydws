# -*- coding: utf-8 -*-

import logging
import urllib2

from tornado.escape import json_encode

from helpers.confhelper import ConfHelper

from base import GFBase

class Sender(GFBase):
    """GF Sender.
    It sends requests from user web server to GF server and receives the
    response from GF.
    """

    def __init__(self, conf_file):
        GFBase.__init__(self, conf_file)


    def forward(self, args):
        """Forward the packet packet to eventer."""
        logging.debug("[GFPROXY] Forwarding to eventer. args: %s", args)
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [("Content-type", "application/json; charset=utf-8")]
            req = urllib2.Request(url=ConfHelper.EVENTER_CONF.url,
                                  data=json_encode(args))
            return opener.open(req).read()
        except Exception as e:
            logging.exception("forward error: %s", e.args)
