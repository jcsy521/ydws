# -*- coding: utf-8 -*-

import pika
from pika.adapters import *
import logging

from helpers.confhelper import ConfHelper

from error import GWException


class RabbitMQMixin(object):

    def connect_rabbitmq(self, host):
        """
        Connect rabbitmq
        """
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=host)
            connection = BlockingConnection(parameters)
            #NOTE: default 50, maybe make it bigger.
            connection.set_backpressure_multiplier(50)
            #NOTE: Write buffer exceeded warning threshold
            #reconnect_rabbitmq = partial(self.__reconnect_rabbitmq, *(connection, host))
            #connection.add_backpressure_callback(reconnect_rabbitmq)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     durable=False,
                                     auto_delete=True)
            channel.queue_declare(queue=self.gw_queue,
                                  durable=False, # not persistent
                                  exclusive=False, 
                                  auto_delete=True) # all client break connection, auto del
            channel.queue_bind(exchange=self.exchange,
                               queue=self.gw_queue,
                               routing_key=self.gw_binding)
            logging.info("[GW] Create GW request queue: %s, binding: %s",
                         self.gw_queue, self.gw_binding)
            logging.info("[GW] Create SI request queue: %s, binding: %s",
                         self.si_queue, self.si_binding)
        except Exception as e:
            logging.exception("[GW] Connect Rabbitmq-server failed. Exception：%s", e.args)
            raise GWException

        return connection, channel

    def reconnect_rabbitmq(self, connection, host):
        """
        This is for catching any unpredictable AMQPConnectionError.
        Release resource for reconnect. 
        """
        logging.info("[GW] Reconnect rabbitmq...") 

        if connection and connection.is_open:
            connection.close()

        def __wait():
            interval = int(ConfHelper.GW_SERVER_CONF.retry_interval)
            logging.error("Retry connect in %d seconds.", interval)
            time.sleep(interval)

        connection = None
        channel = None
        for retry in xrange(int(ConfHelper.GW_SERVER_CONF.retry_count)):
            try:
                connection, channel = self.connect_rabbitmq(host)
                if connection and connection.is_open:
                    logging.info("[GW] Rabbitmq reconnected!")
                    break
                else:
                    __wait()
            except:
                logging.exception("[GW] Connect rabbitmq error.")
                __wait()

        return connection, channel

    def close_rabbitmq(self, connection=None, channel=None):
        """Close rabbitmq.
        """
        if connection and connection.is_open:
            try:
                channel.queue_delete(queue=self.gw_queue)
            except AMQPChannelError as e:
                logging.exception("[GW] Delete gw_queue failed: already delete. Exception: %s",
                                  e.args)
            connection.close()
