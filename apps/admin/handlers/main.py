# -*- coding: utf-8 -*-

import tornado.web

from base import BaseHandler, authenticated


class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
        administrator = self.db.get("SELECT type, is_ajt FROM T_ADMINISTRATOR"
                                    "  WHERE id = %s",
                                    self.current_user.id)
        self.render("index.html",
                    type=administrator.type,
                    is_ajt=administrator.is_ajt)
