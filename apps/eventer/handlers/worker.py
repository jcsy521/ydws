# -*- coding: utf-8 -*-

from threading import Thread
from collections import deque 
import Queue
import logging
import time

from db_.mysql import get_connection
from utils.myredis import MyRedis
from codes.smscode import SMSCode
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper

from packettask import PacketTask


class Worker(object):
    # queue block timeout, do not make it to long and too short.
    BLOCK_TIMEOUT = 1

    def __init__(self, queue, name=None):
        self.queue = queue
        if name is None:
            self.name = id(self)
        else:
            self.name = name
        self.thread = None
        self.db = None
        self.is_alive = False
        self.mobiles = [13693675352, 15901258591]
        self.emails = ['boliang.guan@dbjtech.com',
                       'zhaoxia.guo@dbjtech.com',
                       'xiaolei.jia@dbjtech.com']

    
    def start(self):
        self.db = get_connection()
        self.redis = MyRedis()

        self.thread = Thread(target=self.run)
        self.is_alive = True
        self.thread.start()

    def _run_callback(self, callback):
        try:
            callback()
        except (KeyboardInterrupt, SystemExit):
            self.is_alive = False
        except:
            self.handle_callback_exception(callback)

    def handle_callback_exception(self, callback):
        """This method is called whenever a callback run by the thread
        throws an exception.

        By default simply logs the exception as an error.  Subclasses
        may override this method to customize reporting of exceptions.

        The exception itself is not passed explicitly, but is available
        in sys.exc_info.
        """
        logging.error("Exception in callback %r", callback, exc_info=True)

    def run(self):
        send_time = int(time.time()) 
        while self.is_alive: # TODO: and not self.queue.empty()?
            try:
                packet = self.queue.get(True, self.BLOCK_TIMEOUT)
                queue_len = self.queue.qsize()
                logging.info("[EVENTER] current queue size :%s", queue_len)
                if queue_len >= 30 and (int(time.time()) > send_time):
                    send_time = int(time.time()) + 60*3
                    content = SMSCode.SMS_EVENTER_QUEUE_REPORT % ConfHelper.UWEB_CONF.url_out
                    for mobile in self.mobiles:
                        SMSHelper.send(mobile, content)
                    for email in self.emails:
                        EmailHelper.send(email, content) 
                    logging.info("[EVENTER] Notify EVENTER queue: %s exception to administrator!", queue_len)
            except Queue.Empty:
                pass
            else:
                # TODO: what if we're waiting for gf or lbmp and SystemExit is
                # issued?
                self._run_callback(PacketTask(packet, 
                                              self.db, 
                                              self.redis).run)

    def stop(self):
        self.is_alive = False

    def join(self):
        self.thread.join()
        self.db.close()
        logging.warn("Worker %s joined.", self.name)

    def __del__(self):
        if self.thread and self.thread.is_alive():
            self.stop()
            self.join()


class WorkerPool(object):
    def __init__(self, queue, n=1):
        """
        @param queue: task queue (callbacks)
        @param n: worker number
        """
        self.workers = deque()
        for i in range(n):
            worker = Worker(queue, name=i)
            worker.start()
            self.workers.append(worker)

    def clear(self):
        for worker in self.workers:
            worker.stop()

        for worker in self.workers:
            worker.join()

        self.workers.clear()

