# -*- coding: utf-8 -*-

"""This module is designed for downloading of client.
"""

import tornado.web

from base import BaseHandler

class ClientDownloadHandler(BaseHandler):

    """Show the download page.
    :url /clientdownload
    """

    @tornado.web.removeslash
    def get(self):
        """Jump to the clientDownload html."""
        category = int(self.get_argument('category', 1))
        if category == 1:  # ydws
            self.render('download_ydws.html')
        elif category == 2: # ydwq
            self.render('download_ydwq.html')
        elif category == 3: # ydws-anjietong 
            self.render('download_anjietong.html')
        else:
            self.render('download_ydws.html')
            
