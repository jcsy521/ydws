#!/bin/bash

# swith login.html
cd ./apps/uweb/templates/
rm -f login.html
ln -s ln_login.html login.html
# cd ../../../
# 
# sed -i -e "s/--mode=debug//" -e "s/--logging=DEBUG/--logging=warning/" ./conf/supervisord/services-available/*.conf
