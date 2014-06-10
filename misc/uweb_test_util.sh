#!/bin/bash

cat /tmp/uweb_test.log |awk -F ':' '/Lastposition/  {print $NF}' > /tmp/time.log

#cat /tmp/uweb_test.log |grep 'failed' -c
# 180


