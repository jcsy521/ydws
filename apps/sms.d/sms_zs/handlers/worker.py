# -*- coding: utf-8 -*-

from threading import Thread
from collections import deque 
import logging
import time

from db_.mysql import get_connection
from business.mt import MT


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
        self.mt = MT(self.queue)
    
    def start(self):
        #self.db = get_connection()
        self.thread = Thread(target=self.run)
        self.is_alive = True
        self.thread.start()

    def send_sms(self, sms):
        #mt = MT(self.queue)
        self.mt.send_sms(sms) 

    def run(self):
        while self.is_alive: # TODO: and not self.queue.empty()?
            try:
                if self.queue.qsize() > 0 :
                    s = time.time()
                    sms = self.queue.get(True, self.BLOCK_TIMEOUT)
                    logging.info("Get sms from queue used time :%s", time.time() - s)
                    self.send_sms(sms)
                    logging.info("Send sms to Gateway used time :%s", time.time() - s)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logging.info("[Worker] get exception :%s", e.args)

    def stop(self):
        self.is_alive = False

    def join(self):
        self.thread.join()
        #self.db.close()
        self.mt.db.close()
        logging.warn("Worker %s joined.", self.name)

    def __del__(self):
        if self.thread and self.thread.is_alive():
            self.stop()
            self.join()


class WorkerPool(object):
    def __init__(self, queue, n=5):
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

