#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
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
                self.render("log/details.html",
                            allinfo = allinfo,
                            errorinfo = errorinfo)
           except:
               logging.exception("Details select failed!")
        else:
            self.render("log/details.html",
                        allinfo = '',
                        errorinfo = '',)
