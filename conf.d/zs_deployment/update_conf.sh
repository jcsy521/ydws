#!/bin/bash

# swith login.html
cd ./apps/uweb/templates/
rm -f login.html
ln -s 608_login.html login.html
cd ../../../

sed -i -e "s/--logging=warning/--mode=debug --logging=DEBUG/" ./conf/supervisord/services-available/*.conf
