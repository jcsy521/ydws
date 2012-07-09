# -*- coding: utf-8 -*-

from base import BaseComposer

class GvComposer(BaseComposer):
    GV_TEMPLATE = """<?xml version="1.0" encoding="utf-8" ?><Gis_Req Ver="1.0.0"><HDR Version="1.0.0"><Client><Id>%(username)s</Id><Pwd>%(password)s</Pwd><ServiceID>%(serviceid)s</ServiceID></Client><RequestorID>%(group)s</RequestorID></HDR><RGR><Position levelOfConf=""><Point id="s1" srsName="WGS-84"><pos srsName="WGS-84" dimension="2" isEncrypted="false" isOriginalCoord="false">%(lon)s %(lat)s</pos></Point></Position><MaximumResponses>1</MaximumResponses></RGR></Gis_Req>"""

    def __init__(self, args):
        
        self.args = args
        username = args['username']
        password = args['password']
        group = args['group']
        serviceid = args['serviceid'] 
        lon = args['lon']
        lat = args['lat']
        self.template = self.GV_TEMPLATE % locals()
