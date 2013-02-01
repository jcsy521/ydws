#!/usr/bin/python
# -*- coding: UTF-8 -*-

import tornado.database

from base import authenticated,BaseHandler


class Detail(BaseHandler):
    
    @authenticated
    def get(self):
        id = self.get_argument("id",'')
        if id:
            try:
                allinfo = self.db.query("SELECT * FROM T_LOG_DETAILS"
                                        "  where id = %s", id)
                errorinfo = self.db.query("SELECT * FROM T_LOG_ERROR"
                                          "  where about = %s", id)
                self.render("details.html",
                            allinfo = allinfo,
                            errorinfo = errorinfo,)
                return
            except:
                logging.error("Details select failed!")
        else:
            self.render("details.html",
                        allinfo = '',
                        errorinfo = '',)
            return
