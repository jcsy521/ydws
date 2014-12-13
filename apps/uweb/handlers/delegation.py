# -*- coding: utf-8 -*-

"""This module is designed for delegation.
"""

import tornado.web

from helpers.uwebhelper import UWebHelper
from constants import UWEB

from base import BaseHandler


class DelegationHandler(BaseHandler):
    
    @tornado.web.removeslash
    def get(self, uid, tid, sim):
        """Redirect to main.
        """
        sign = self.get_argument('s', None)
        if not sign or not UWebHelper.check_sign(sign, 
                                                 ''.join([uid, tid, sim])):
            raise tornado.web.HTTPError(401)

        self.bookkeep(dict(uid=uid, 
                           tid=tid, 
                           sim=sim,
                           cid=UWEB.DUMMY_CID,
                           oid=UWEB.DUMMY_OID))
        #NOTE: header is import. 
        self.set_header("P3P", "CP=CAO PSA OUR")
        self.redirect("/?from=delegation")
