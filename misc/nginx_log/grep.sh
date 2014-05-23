#!/bin/bash

# cat
cat /var/log/nginx/uweb/access.log |grep -E 'download/terminal|static/terminal' |grep '22/May/2014' > nginx.log

# python
python download_script.py

# cat 
cat enc_nginx.log
