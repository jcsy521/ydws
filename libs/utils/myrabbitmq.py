# -*- coding: utf-8 -*-

import logging
import time
import pika
import json
from pika.adapters import *
from pika.exceptions import AMQPConnectionError
from functools import partial
from constants import MQ

from helpers.confhelper import ConfHelper


class MyRabbitMQ(object):

    """Simple Queue with RabbitMQ Backend"""

    def __init__(self, queue):
        """ 
        """
        self.host = ConfHelper.RABBITMQ_CONF.host       
        self.exchange = 'ydws_exchange'
        self.queue = queue
        self.connection, self.channel = self.connect_rabbitmq() 

    def connect_rabbitmq(self):
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=self.host)
            connection = BlockingConnection(parameters)
            # # Write buffer exceeded warning threshold
            # reconnect_rabbitmq = partial(self.__reconnect_rabbitmq, (host,))
            # connection.add_backpressure_callback(reconnect_rabbitmq)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     type='direct', # send body according the routing_key
                                     durable=False, # survive a reboot of RabbitMQ
                                     auto_delete=True) # remove when no more queues are bound to it.

            channel.queue_declare(queue=self.queue,
                                  durable=False,  # do not keep the data persistent.
                                  exclusive=False, # keep queue exist even if no body in queue.
                                  auto_delete=True) # delete after consumer cancels or disconnects

            # Bind the queue to the specified exchange
            channel.queue_bind(exchange=self.exchange,
                               queue=self.queue,
                               routing_key=self.queue)
            logging.info("[MYRABBITMQ] Create rabbitmq successful. host: %s, exchange:%s, queue: %s",
                         self.host, self.exchange, self.queue)

        except:
            logging.info("[MYRABBITMQ] Create rabbitmq successful. host: %s, exchange:%s, queue: %s",
                         self.host, self.exchange, self.queue)
            # #TODO:
            # logging.exception("[GW] Connect Rabbitmq-server failed. Exception：%s", e.args)
            # raise GWException

        return connection, channel

    def __wait(self):
        logging.error("[MYRABBITMQ] Retry connect in %d seconds.", MQ.RETRY_INTERVAL)
        time.sleep(MQ.RETRY_INTERVAL)

    def __reconnect_rabbitmq(self):
        """
        This is for catching any unpredictable AMQPConnectionError.
        Release resource for reconnect. 
        """
        logging.debug("[MYRABBITMQ] Reconnect rabbitmq...") 
        if self.connection and self.connection.is_open:
            self.connection.close()

        connection = None
        channel = None
        for retry in xrange(MQ.RETRY_COUNT):
            try:
                connection, channel = self.connect_rabbitmq()
                if connection and connection.is_open:
                    logging.info("[MYRABBITMQ] Rabbitmq reconnected!")
                    break
                else:
                    self.__wait()
            except:
                logging.exception("[MYRABBITMQ] Connect rabbitmq error.")
                self.__wait()

        if not connection or (not connection.is_open):
            #BIG NOTE: it should never occurs.
            logging.error("[MYRABBITMQ] After reconnect too many times, rabbitmq is still does not work well.")

        return connection, channel

    def put(self, item):
        """Put the item into the queue.

        :arg item: str or other python object. Before put into mq, it should be casted to str.
        """
        #TODO: optimize it.
        body = json.dumps(item)
        logging.info("[MYRABBITMQ] Put body in mq. body: %s", body)
        try:
            # make message not persistent
            properties = pika.BasicProperties(delivery_mode=1,)
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=self.queue,
                                       body=body,
                                       properties=properties)

        except AMQPConnectionError as e:
            logging.exception("[MYRABBITMQ] Put body in mq failed. Exception: %s", e.args)
            self.connection, self.channel = self.__reconnect_rabbitmq()

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue. 

        :arg block: bool. If true, it will block until one message got. If False, None maybe be found.
        :arg timeout: int, in seconds.

        workflow:
        if block:
            if timeout:
                pass
            else:
                timeout = 1 minute

            while timeout is not passed:
                body = basic_get()
                if body:
                    return body
                else:
                    continue
        else:
            basic_get()

        #NOTE: If nothing can be found from the queue, the following get through basic_get() method:
        <Basic.GetEmpty(['cluster_id='])> None None

        """
        def _get():          
            body = None
            try:  
                method, header, body = self.channel.basic_get(queue=self.queue)
                if method.NAME == 'Basic.GetEmpty':
                    pass            
                else:
                    self.channel.basic_ack(delivery_tag=method.delivery_tag)            
            except AMQPConnectionError as e:
                logging.exception("[MYRABBITMQ] Put body in mq failed. Exception: %s", e.args)
                self.connection, self.channel = self.__reconnect_rabbitmq()
            return body

        if block:
            if timeout:
                pass
            else:
                timeout = 60*1  #TODO: 1 minutes.

            _start_time = int(time.time())

            while True:
                time.sleep(1)
                _end_time = int(time.time())
                if (_end_time - _start_time) >= timeout:
                    body = _get()
                    break

                body = _get()
                if not body:
                    continue    
                else:
                    break                                         
        else:
            body = _get()

        if body:
            body = json.loads(body)
        return body

    def close(self):
        """Close rabbitmq.

        1. delete the queue
        2. close the connection
        """
        if self.connection and self.connection.is_open:
            #TODO: delete queue?
            # try:
            #     self.channel.queue_delete(queue=self.queue)
            # except AMQPChannelError as e:
            #     logging.exception("[MYRABBITMQ] Delete gw_mq failed: already delete. Exception: %s",
            #                       e.args)
            self.connection.close()   

    def __del__(self):
        self.close()
