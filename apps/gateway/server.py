#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site

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
from checkpofftimeout import CheckpofftimeoutHandler
from lqterminals import LqterminalHandler

def shutdown(gwserver, processes):
    try:
        for process in processes:
            if process and process.is_alive():
                process.join()
            logging.warn("Process: %s ", process)
        gwserver.stop()

    except:
        pass

def usage():
    print "python26 server.py --conf=/path/to/conf_file"

def check_poweroff_timeout_thread():
    logging.info("[GW] Check terminals poweroff timeout thread start...")
    cpt = CheckpofftimeoutHandler() 
    try:
        while True:
            time.sleep(60)
            cpt.check_poweroff_timeout()
    except Exception as e:
        logging.exception("[GW] Start check terminals poweroff timeout thread failed.")

def lq_terminals_thread():
    logging.info("[GW] Lq terminals thread start...")
    lth = LqterminalHandler()
    try:
        while True:
            time.sleep(60)
            lth.lq_terminals()
    except Exception as e:
        logging.exception("[GW] Start lq terminal thread failed.")

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
        logging.warn("[gateway] running on: localhost")
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
        thread.start_new_thread(lq_terminals_thread, ())
        thread.start_new_thread(check_poweroff_timeout_thread, ())
        for p in processes:
            p.start()
        for p in processes:
            # NOTE: just to put into join queue, it will work until process
            # finished
            p.join()

    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[gateway] Exit Exception")
    finally:
        logging.warn("[gateway] shutdown...")
        shutdown(gwserver, processes)
        logging.warn("[gateway] stopped. Bye!")


if __name__ == '__main__':
    main()
