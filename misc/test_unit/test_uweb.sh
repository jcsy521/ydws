============
# Part curl 
===========

# android login
curl -i -X POST -d 'username=15919176710' -d 'password=111111' http://drone-009:6301/android
curl -i -X POST  http://drone-009:6301/logintest/android

# ios login
curl -i -X POST -d 'username=15919176710' -d 'password=111111' -d 'iosid=testiosid'  http://drone-009:6301/ios
curl -i -X POST  http://drone-009:6301/logintest/ios
curl -i -X POST  http://drone-009:6301/logintest


==============
# Part httpie
==============

# Item login 
# NOTE: in /home/w_jiaxiaolei/.httpie/sessions/drone-009_6301/jia.json, cookie is found

# For logintest
http --session jia -f POST  http://drone-009:6301/logintest

# For web browser 
#NOTE: Get a captcha and keep it in cookie. 
#http --session jia -f POST  http://drone-009:6301/captcha

# For web browser, 5503's captchahash is 4b85256c4881edb6c0776df5d81f6236,  you can set it in sessions/session_name/.json 
http --session jia -f POST  http://drone-009:6301/login username=15919176710 password=111111 captcha=5503

# For Android 
http --session jia -f POST  http://drone-009:6301/android username=15919176710 password=111111

# For IOS 
http --session jia -f POST  http://drone-009:6301/ios username=15919176710 password=111111 iosid=testiosid

# Item track
# NOTE: --json: means the data is json
http --json --session jia -f POST  http://drone-009:6301/track cellid_flag=0 start_time=1407945600 end_time=1407999846 tid=T123SIMULATOR


