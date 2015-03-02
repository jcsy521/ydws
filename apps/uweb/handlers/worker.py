# -*- coding: utf-8 -*-

"""This module is designed for multi-thread.

Worker and Workers depend on the PriorityQueue created in Uweb-server. 

"""

from threading import Thread
from collections import deque 
import logging
import time

from db_.mysql import get_connection


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
    
    def start(self):
        self.db = get_connection()
        self.thread = Thread(target=self.run)
        self.is_alive = True
        self.thread.start()

    def _run_callback(self, callback):
        try:
            callback(db=self.db)
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
        while self.is_alive: # TODO: and not self.queue.empty()?
            try:
                if self.queue.qsize() > 0 :
                    p, callback = self.queue.get(True, self.BLOCK_TIMEOUT)
                    self._run_callback(callback)
                else:
                    time.sleep(1)
                    #time.sleep(0.1)
            except Exception as e:
                logging.info("[Worker] get exception :%s", e.args)

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
