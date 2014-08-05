#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import linecache
import logging
import urllib2

from tornado.escape import json_encode

class EventerHelper(object):

    url = 'http://192.168.1.5:5001'
    file_path = '/var/log/supervisor/eventer/'
    start_time = "20130715 17:44:52"
    end_time = "20130722 17:49:11"

    @classmethod
    def sendpacket(self):

        files = os.listdir(self.file_path)
        for file in files:
            print self.file_path+file
            lines= linecache.getlines(self.file_path+file)
            linecache.updatecache(self.file_path+file)
            p1 = re.compile("Get request from sender", re.I)
            for num in range(len(lines)):
                if p1.search(lines[num]):
                    if '20%s' % lines[num][3:18] > self.start_time and '20%s' % lines[num][3:18] < self.end_time:
                        packet = lines[num+1]
                        if 'ACB2012777' in packet and 'T3' in packet:
                            print packet
                            #self.forward(packet)
    @classmethod
    def forward(self, args):
        """Forward the packet packet to eventer."""
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [("Content-type", "application/json; charset=utf-8")]
            req = urllib2.Request(url=self.url,
                                  data=args)
            return opener.open(req).read()
        except Exception as e:
            logging.exception("forward error: %s", e.args)

if __name__ == "__main__":
    EH = EventerHelper()
    s = EH.sendpacket()
