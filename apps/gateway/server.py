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
try:
    options['logging'].set('info')
except:
    options.logging='info'

from utils.myredis import MyRedis
from db_.mysql import DBConnection
from helpers.confhelper import ConfHelper

from mygwserver import MyGWServer

def shutdown(gwserver, processes):
    """Shut down the server.

    workflow:
    stop process
    close gw server
    """
    try:
        for p in processes:
            #if process and process.is_alive():
            #    process.join()
            #logging.warn("Process: %s ", process)
            p.terminate()
            logging.info("[GW] Process is terminated. name: %s, pid: %s, exitcode: %s", 
                         p.name, p.pid, p.exitcode)
        for p in processes:
            p.join()
        gwserver.stop()
    except Exception as e:
        logging.exception("[GW] Shutdown failed. Exception: %s", e.args)
        pass

def usage():
    print "python server.py --conf=/path/to/conf_file"

def main():
    """Main method.

    """
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
    #db = DBConnection().db

    gwserver = None
    processes = None
    try:
        logging.warn("[GW] Running on: localhost. Parent process: %s, Current process: %s", 
                     os.getppid(), os.getpid())

        gwserver = MyGWServer(options.conf)

        gwserver.redis = redis
        #gwserver.db = db

        gw_send = Process(name='GWSender',
                          target=gwserver.consume,
                          args=(ConfHelper.RABBITMQ_CONF.host,))

        gw_recv = Process(name='GWReceiver',
                          target=gwserver.publish,
                          args=(ConfHelper.RABBITMQ_CONF.host,))

        processes = (gw_send, gw_recv,)
        for p in processes:
            p.start()
            logging.info("[GW] Process name: %s, pid: %s start.",
                         p.name, p.pid)
        #NOTE: It's maybe unused here. 
        for p in processes:
            # NOTE: just to put into join queue, it will work until process
            # finished
            p.join()

    except KeyboardInterrupt:
        try:
            for p in processes:
                logging.info("[GW] Process terminate. name: %s, pid: %s, exitcode: %s",
                             p.name, p.pid, p.exitcode)
                p.terminate()
            for p in processes:
                p.join()
            thread.exit()
        except SystemExit:
            logging.info("[GW] Process stop...")
        logging.error("[GW] Ctrl-C is pressed.")
    except:
        logging.exception("[GW] Exit Exception")
    finally:
        logging.warn("[GW] Shutdown...")
        shutdown(gwserver, processes)
        logging.warn("[GW] Stopped. Bye!")


if __name__ == '__main__':
    main()
