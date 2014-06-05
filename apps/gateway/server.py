#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import os

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import thread
import time
import signal
import logging
import multiprocessing
from multiprocessing import Process, Queue, Pool
from threading import Thread

import tornado
from tornado.options import define, options
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options['logging'].set('info')

from utils.myredis import MyRedis
from db_.mysql import DBConnection
from helpers.confhelper import ConfHelper

from mygwserver import MyGWServer

def shutdown(gwserver, processes, db):
    try:
        for process in processes:
            if process and process.is_alive():
                process.join()
            logging.warn("Process: %s ", process)
            process.terminate()
        db.close()
        gwserver.stop()

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

    gwserver = None
    processes = None
    try:
        logging.warn("[gateway] running on: localhost. Parent process: %s", os.getpid())
        gwserver = MyGWServer(options.conf)
        gwserver.redis = redis
        gwserver.db = db
        gw_send = Process(name='GWSender',
                          target=gwserver.consume,
                          args=(ConfHelper.RABBITMQ_CONF.host,))
        gw_recv = Process(name='GWReceiver',
                          target=gwserver.publish,
                          args=(ConfHelper.RABBITMQ_CONF.host,))
        processes = (gw_send, gw_recv,)
        for p in processes:
            p.start()
        for p in processes:
            # NOTE: just to put into join queue, it will work until process
            # finished
            p.join()

    except KeyboardInterrupt:
        try:
            for p in processes:
                p.terminate()
            thread.exit()
        except SystemExit:
            logging.info("[GW] Threads stop...")
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[gateway] Exit Exception")
    finally:
        logging.warn("[gateway] shutdown...")
        shutdown(gwserver, processes, db)
        logging.warn("[gateway] stopped. Bye!")


if __name__ == '__main__':
    main()
