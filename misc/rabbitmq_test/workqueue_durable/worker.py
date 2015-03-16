#!/usr/bin/env python
#coding=utf8
import pika
import time
 
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()
 
channel.queue_declare(queue='hello')
 
def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)
    time.sleep(5)
    print " [x] Done" 
    ch.basic_ack(delivery_tag = method.delivery_tag)
 
# Fair dispatch
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, 
                      queue='hello', 
                      no_ack=False)
 
print ' [*] Waiting for messages. To exit press CTRL+C'
channel.start_consuming()
