#!/bin/python

"""
"""
from decimal import Decimal

f = open('/tmp/time.log')
#f = open('a.txt')
count = 0
max_time=Decimal()
total_time=Decimal()
for line in f:
    #print 'line', line,type(line)
    time=Decimal(line)
    if time > max_time:
        max_time = time
    count = count+1
    total_time = total_time + time

print 'success:', count
print 'max_time:', max_time 
print 'total_time:', total_time 
print 'average_time:', total_time/count  

f.close()
