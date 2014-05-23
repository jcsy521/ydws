import re
import linecache


f2 = open('enc_nginx.log', 'wa')
p = re.compile("/download/terminal", re.I)
lines= linecache.getlines('nginx.log')
#lines= linecache.getlines('access.log')
for i, line in enumerate(lines):
    if p.search(line):
        f2.write(line)
        ip = line[:14]
        p2 = re.compile(ip, re.I)
        p3 = re.compile('/static/terminal', re.I)
        tmp = lines[i+1:]
        for j in range(len(tmp)):
            l = tmp[j]
            if p2.search(l) and p3.search(l):
                f2.write(l)
                break
f2.close()

