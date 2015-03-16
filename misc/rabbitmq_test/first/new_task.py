import pika
import sys

host='drone-205'
connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))

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
