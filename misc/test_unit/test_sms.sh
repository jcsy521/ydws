============
# Part curl 
===========

curl -i -X  POST  www.ichebao.net -d  mobile=13011292217  -d content=jiatest222 www.ichebao.net/sms/mt

curl -i -X  POST  www.ichebao.net -d  mobiles=13011292217  -d msg=jiatest222 www.ichebao.net/sms/mt


==============
# Part httpie
==============

sudo http  -f POST  www.ichebao.net/sms/cmppmt mobile=13011292217 content=jiatest

sudo http  -f POST  www.ichebao.net/sms/mt mobiles=13011292217 msg=jiatest222






