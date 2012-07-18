#!/usr/bin/env python
# -*- coding: utf-8 -*-

from struct import unpack_from

def ip2long(ip):
    return reduce(lambda x,y: (x<<8) + y, map(int, ip.strip().split('.')))

def long2ip(l):
    s = []
    for i in range(4):
        s.insert(0, str(l & 0xff))
        l >>= 8
    return '.'.join(s)


class QQWry(object):
    def close(self):
        self.rec = []
        self.index = 0
        
    def __init__(self):
        self.close()
    
    def read3Bytes(self, buf, offset):
        return unpack_from('<L', buf[offset:offset + 3] + '\0')[0]

    def readString(self, buf, offset, depth):
        if offset <= 0 or depth > 5: return ''
        mode = ord(buf[offset])
        if mode == 1 or mode == 2:
            return self.readString(buf, self.read3Bytes(buf, offset+1), depth+1)
        pos = buf.find('\0', offset)
        if pos >= 0:
            return buf[offset:pos]
        else:
            return buf[offset:]
        
    def readAddr(self, buf, offset, depth):
        if offset <= 0 or depth > 5: return [''] * 2
        mode = ord(buf[offset])
        if mode == 1:
            return self.readAddr(buf, self.read3Bytes(buf, offset+1), depth+1)
        country = self.readString(buf, offset, depth)
        if mode == 2:
            offset += 4
        else:
            offset += len(country) + 1
        area = self.readString(buf, offset, depth)
        return [country, area]
        
    def open(self, f):
        self.close()
        pos = f.tell()
        f.seek(0)
        buf = f.read()
        f.seek(pos)
        pos, lastIndex = unpack_from('<LL', buf)
        while pos <= lastIndex:
            ip_begin = unpack_from('<L', buf, pos)[0]
            offset = self.read3Bytes(buf, pos + 4)
            r = [ip_begin, unpack_from('<L', buf, offset)[0]]
            r.extend(self.readAddr(buf, offset + 4, 0))
            self.rec.append(tuple(r))
            pos += 7

    def __len__(self):
        return len(self.rec)

    def __iter__(self):
        return self
    
    def next(self):
        if self.index == self.__len__():
            raise StopIteration
        self.index += 1
        return self.rec[self.index - 1]
    
    def getRecordByIndex(self, idx):
        if 0 <= idx < self.__len__():
            return self.rec[idx]
        return None
    
    def getRecordByIPLong(self, l):
        head, tail, m, r = 0, self.__len__(), -1, None
        while True:
            mid = (head + tail) >> 1
            if mid == m: break
            m, mr = mid, self.rec[mid]
            if mr[0] <= l <= mr[1]:
                r = mr
                break
            if mr[0] > l:
                tail = mid
            else:
                head = mid
        return r

    def getRecordByIP(self, ip):
        return self.getRecordByIPLong(ip2long(ip))


if __name__ == '__main__':
    db = QQWry()
    with open('./qqwry.dat', 'rb') as f:
        db.open(f)
    # ip = raw_input('Please now input your IP address:')
    ip = "121.1.6.162"
    r = db.getRecordByIP(ip)
    if r is not None:
        for i in r:
            if isinstance(i, str):
                print i.decode('gbk')
            else:
                print i

