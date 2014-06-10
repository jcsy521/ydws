#!/bin/bash

count=10
echo $count
for ((i=1;i<$count;i++));do
  echo 'start script: '$i
  #python uweb_test.py>>/tmp/uweb_test.log
  python uweb_test.py &
done
