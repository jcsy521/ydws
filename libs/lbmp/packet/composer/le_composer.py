# -*- coding: utf-8 -*-

from base import BaseComposer

class LeComposer(BaseComposer):

    LE_TEMPLATE = """<?xml version="1.0" encoding="GB2312"?><svc_init ver="2.0.0"><hdr ver="2.0.0"><client><id>%(username)s</id><pwd>%(password)s</pwd><serviceid>%(serviceid)s</serviceid></client><requestor><id>%(group)s</id></requestor></hdr><slir ver="2.0.0" res_type="SYNC"><msids><msid enc="ASC" type="MSISDN">%(sim)s</msid></msids><eqop><resp_req type="LOW_DELAY"/><hor_acc qos_class="BEST_EFFORT">200</hor_acc></eqop><geo_info><CoordinateReferenceSystem><Identifier><code>4326</code><codeSpace>EPSG</codeSpace><edition>6.1</edition></Identifier></CoordinateReferenceSystem></geo_info><loc_type type="CURRENT_OR_LAST"/><prio type="HIGH"/></slir></svc_init>"""

    def __init__(self, args):
        
        self.args = args
        username = args['username']
        password = args['password']
        serviceid = args['serviceid'] 
        group = args['group']
        sim = args['sim']
        self.template = self.LE_TEMPLATE % locals()
