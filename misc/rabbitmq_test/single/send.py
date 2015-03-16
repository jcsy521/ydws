#!/usr/bin/env python
#coding=utf8
import pika
 
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()
 
channel.queue_declare(queue='hello')

channel.basic_publish(exchange='', 
                      routing_key='hello', 
                      body='hello world!')
print " [x] Sent %r" % ('hello world!',)
connection.close()
