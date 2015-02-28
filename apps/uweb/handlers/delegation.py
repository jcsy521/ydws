# -*- coding: utf-8 -*-

"""This module is designed for delegation.
"""

import tornado.web

from helpers.uwebhelper import UWebHelper
from base import BaseHandler


class DelegationHandler(BaseHandler):

    """Delegation for admin server.

    :url /delegation/5Luj5a6i5pON5L2c/{uid}/{tid}/{sim}/{cid}/{oid}
    """

    @tornado.web.removeslash
    def get(self, uid, tid, sim, cid, oid):
        """Redirect to main.
        """
        sign = self.get_argument('s', None)
        if not sign or not UWebHelper.check_sign(sign,
                                                 ''.join([uid, tid, sim, cid, oid])):
            raise tornado.web.HTTPError(401)

        self.bookkeep(dict(uid=uid,
                           tid=tid,
                           sim=sim,
                           cid=cid,
                           oid=oid))

        # NOTE: header is import.
        self.set_header("P3P", "CP=CAO PSA OUR")
        self.redirect("/?from=delegation")
