#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import signal
import logging
import multiprocessing
from multiprocessing import Process, Queue, Pool
from threading import Thread

from utils import options
options.define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
options.options['logging'].set('info')

from utils.myredis import MyRedis
from db_.mysql import DBConnection
from helpers.confhelper import ConfHelper

from siserver import SIServer
from gatewayserver import GatewayServer

def shutdown(servers, processes):
    try:
        for process in processes:
            if process and process.is_alive():
                process.join()
            logging.warn("Process: %s ", process)
        for server in servers:
            server.stop()

    except:
        pass

def main():
    options.parse_command_line()
    ConfHelper.load(options.options.conf)
    redis = MyRedis()
    db = DBConnection().db
    si_requests_queue = Queue()
    gw_requests_queue = Queue()

    servers = None
    processes = None
    try:
        logging.warn("[gateway] running on: localhost")
        siserver = SIServer(options.options.conf)
        gwserver = GatewayServer(options.options.conf)
        servers = (siserver, gwserver)
        for server in servers: 
            server.redis = redis
            server.db = db
        si_process = Process(name='SIServer',
                             target=siserver.handle_si_connections,
                             args=(si_requests_queue, gw_requests_queue))
        gw_send = Process(name='GWSender',
                          target=gwserver.send,
                          args=(gw_requests_queue,))
        gw_recv = Process(name='GWReceiver',
                          target=gwserver.recv,
                          args=(si_requests_queue, gw_requests_queue))
        processes = (si_process, gw_send, gw_recv)
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
        shutdown(servers, processes)
        logging.warn("[gateway] stopped. Bye!")


if __name__ == '__main__':
    main()
