# -*- coding: utf-8 -*-

from base import BaseComposer

class ZsLeComposer(BaseComposer):

    LE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?><lbsReq ver="1.0"><client><id>%(id)s</id><pwd>%(pwd)s</pwd><serviceid>%(serviceid)s</serviceid></client><simcard>%(simcard)s</simcard></lbsReq>"""

    def __init__(self, args):
        
        self.args = args
        id = "zsds20120224" 
        pwd = "zsds20120224"
        serviceid = "zsds"
        simcard = args['simcard']
        self.template = self.LE_TEMPLATE % locals()
