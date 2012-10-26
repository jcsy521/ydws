# -*- coding: utf-8 -*-

from base import BaseComposer

class SubscriptionComposer(BaseComposer):

    SUBSCRIPTION_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?><sync_req><head><id>%(id)s</id><pwd>%(pwd)s</pwd></head><body><area>%(area)s</area><serviceid>%(serviceid)s</serviceid><appName>%(appName)s</appName><phoneList><phone><phoneNum>%(phoneNum)s</phoneNum><action>%(action)s</action><position_type>A</position_type><ue_type>1</ue_type><servicetype>AL</servicetype><status>A</status></phone></phoneList></body></sync_req>"""

    def __init__(self, args):

        self.args = args
        id = args['id']
        pwd = args['pwd']
        area = args['area']
        serviceid = args['serviceid'] 
        appName = args['appName']
        phoneNum = args['phoneNum']
        action = args['action']
        self.template = self.SUBSCRIPTION_TEMPLATE % locals()
