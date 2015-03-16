#!/usr/bin/env python
#coding=utf8
import pika
import sys
 
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))

channel = connection.channel()
 
#channel.queue_declare(queue='hello')
channel.queue_declare(queue='jiaxiaolei')

message = ' '.join(sys.argv[1:]) or "Hello World!"
 
channel.basic_publish(exchange='', 
                      routing_key='jiaxiaolei', 
                      body=message)
print " [x] Sent %r" % (message,)
connection.close()
