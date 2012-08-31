#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging

import tornado
from tornado.options import define, options
options.define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options.options['logging'].set('info')

from utils.myredis import MyRedis
from db_.mysql import DBConnection
from helpers.confhelper import ConfHelper

from mysiserver import MySIServer

def shutdown(server):
    try:
        server.stop()
    except:
        pass

def usage():
    print "python26 server.py --conf=/path/to/conf_file"

def main():
    tornado.options.parse_command_line()
    if not ('conf' in options):
        import sys
        usage()
        sys.exit(1)

    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    ConfHelper.load(options.conf)
    redis = MyRedis()
    db = DBConnection().db

    siserver = None
    try:
        logging.warn("[siserver] running on: localhost")
        siserver = MySIServer(options.conf)
        siserver.redis = redis
        siserver.db = db
        siserver.handle_si_connections()

    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[siserver] Exit Exception")
    finally:
        logging.warn("[siserver] shutdown...")
        shutdown(siserver)
        logging.warn("[siserver] stopped. Bye!")


if __name__ == '__main__':
    main()
