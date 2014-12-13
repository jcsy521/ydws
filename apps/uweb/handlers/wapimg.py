# -*- coding: utf-8 -*-

"""This module is designed for the wapimg.
"""

import logging

import tornado.web

from base import BaseHandler
from helpers.confhelper import ConfHelper


class WapImgHandler(BaseHandler):
    """Play with wapimg and uweb url and download url."""

    @tornado.web.removeslash
    def get(self):
        clon = self.get_argument('clon', 0)
        clat = self.get_argument('clat', 0)
        self.render('wapimg.html',
                    clon=clon,
                    clat=clat,
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    home_url=ConfHelper.UWEB_CONF.url_out,
                    android_download=ConfHelper.UWEB_CONF.url_out + '/instruction/android')
        logging.info("[UWEB] Render to wapimg. clon: %s, clat: %s.",
                     clon, clat)

