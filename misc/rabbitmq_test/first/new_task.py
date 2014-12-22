import pika
import sys

#connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
connection = pika.BlockingConnection(pika.ConnectionParameters(host='drone-205'))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.1.105'))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1'))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.1.102'))
channel = connection.channel()

channel.queue_declare(queue='si_requests_queue',
                      durable=False)

#NOTE:
message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(exchange='',
                      routing_key='si_requests_queue',
                      body=message,
                      properties=pika.BasicProperties(
                          delivery_mode=1, # make message persistent
                      ))

print "[x] Sent %r" % message
connection.close()
