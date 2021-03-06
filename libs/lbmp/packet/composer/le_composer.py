# -*- coding: utf-8 -*-

from base import BaseComposer

class LeComposer(BaseComposer):

    LE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?><lbsReq ver="1.0"><client><id>%(id)s</id><pwd>%(pwd)s</pwd><serviceid>%(serviceid)s</serviceid></client><simcard>%(simcard)s</simcard></lbsReq>"""

    def __init__(self, args):
        
        self.args = args
        id = args['id']
        pwd = args['pwd']
        serviceid = args['serviceid'] 
        simcard = args['simcard']
        self.template = self.LE_TEMPLATE % locals()
