import re

log = open('/var/log/supervisor/gateway/error.log', 'r')
p1 = re.compile("355C000064", re.I)
p2 = re.compile("recv", re.I)
p3 = re.compile("(T3|T13|T14|T15|T16)", re.I)
p4 = re.compile("T2,", re.I)
for line in log:
    if p1.search(line) and p2.search(line):
        if p3.search(line):
            t = line[2:18]
            ldata = line.split(',')
            c = ldata[5]
            s = ldata[15].split(':')[2]
            print t,c,s+"%"
        elif p4.search(line):
            t = line[2:18]
            s = line.split(',')[6].split(':')[2]
            print t,"T2",s+"%"

log.close()
