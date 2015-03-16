#!/bin/bash
count=1000
count=2
for((i=1;i<$count;i++));do
    curl -i -X GET 'http://xiaolei.ichebao.net/download/terminal?sn=CBBJTEAM01&v=ZJ200_1.5'> b.lua
done

