# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_ios_push_list_key, get_ios_id_key, get_ios_badge_key,\
     get_android_push_list_key, get_terminal_info_key, get_location_key, get_lastinfo_time_key, DUMMY_IDS
from utils.checker import check_sql_injection, check_phone
from utils.public import get_group_info_by_tid
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER, GATEWAY
from base import BaseHandler, authenticated
from helpers.notifyhelper import NotifyHelper
from helpers.queryhelper import QueryHelper 
from helpers.lbmphelper import get_locations_with_clatlon
from helpers.downloadhelper import get_version_info 
from helpers.confhelper import ConfHelper

class BindHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        self.render("bind.html") 


class UnBindHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        self.render("unbind.html") 
