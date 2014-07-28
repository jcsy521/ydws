#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import thread

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import signal
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from Queue import Queue

define('port', type=int, default=4000)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
try:
    options['logging'].set('warning')
except:
    options.logging='warning'

from gf.proxy.sender import Sender

from handlers.main import MainHandler
from handlers.realtime import RealtimeHandler
from handlers.terminal import TerminalHandler
from handlers.defend import DefendHandler
from handlers.query import QueryHandler
from handlers.unbind import UNBindHandler

class Application(tornado.web.Application):

    def __init__(self, gf_sender, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/realtime/*", RealtimeHandler),
            (r"/terminal/*", TerminalHandler),
            (r"/defend/*", DefendHandler),
            (r"/query/*", QueryHandler),
            (r"/unbind/*", UNBindHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #debug=debug,
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.gf_sender = gf_sender


def shutdown(http_server, gf_sender):
    try:
        if http_server:
            # old version of tornado does not support stop
            if hasattr(http_server, 'stop'):
                http_server.stop()
            tornado.ioloop.IOLoop.instance().stop()

        if gf_sender:
            gf_sender.destroy()
    except:
        # the server might have not start
        pass


def main():
    tornado.options.parse_command_line()
    if not ('port' in options and 'conf' in options):
        import sys
        usage()
        sys.exit(1)

    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    gf_sender = None
    http_server = None
    try:
        gf_sender = Sender(options.conf)
        gf_sender.send_queue = Queue()
        gf_sender.wait_response_queue = {}
        
        thread.start_new_thread(gf_sender.periodic_send, ())
        
        app = Application(gf_sender, debug=debug_mode)

        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        http_server.listen(options.port)
        logging.warn("[gfsender] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
        gf_sender.logout()
    except:
        logging.exception("[gfsender] Exit Exception")
    finally:
        logging.warn("[gfsender] shutdown...")
        shutdown(http_server, gf_sender)
        logging.warn("[gfsender] stopped. Bye!")


def usage():
    print "python26 server.py --conf=/path/to/conf_file --port=port_num"


if __name__ == '__main__':
    main()
