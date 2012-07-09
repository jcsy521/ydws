# -*- coding: utf-8 -*-

"""
This helper helps to communicate with eventer. You have to prepare all the fields
a specific packet needs and the helper will pass these fields to eventer via the
according url. Anyone who wants to send async info should use this helper, by
now, uweb, gfsender use it.
"""

import logging
import urllib2

from tornado.escape import json_encode

from confhelper import ConfHelper


class EventerHelper(object):

    @classmethod
    def forward(self, args):
        """Forward the packet packet to eventer."""
        logging.debug("forwarding...")
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [("Content-type", "application/json; charset=utf-8")]
            req = urllib2.Request(url=ConfHelper.EVENTER_CONF.url,
                                  data=json_encode(args))
            return opener.open(req).read()
        except Exception as e:
            logging.exception("forward error: %s", e.args)

