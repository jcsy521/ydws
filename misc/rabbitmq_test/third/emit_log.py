import pika
import sys

host='drone-205'
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=host))
channel = connection.channel()

channel.exchange_declare(exchange='logs_test',
                         type='fanout')

message = ' '.join(sys.argv[1:]) or "info: Hello World!"
channel.basic_publish(exchange='logs_test',
                      routing_key='',
                      body=message)

print " [x] Sent %r" % (message,)
connection.close()
 

