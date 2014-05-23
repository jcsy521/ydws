
#!/bin/bash

# subscription
#curl -d '{"sim":"14778477173", "action":"A"}' http://app01:3001/subscription

# le
#curl -d '{"sim":"14778742471","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le
#curl -d '{"sim":"14778477173","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le

# ge
curl -i -X POST  -d '{"lons":[408339504],"lats":[80418276]}' localhost:3000/ge
#curl -i -X POST  -d '{"lons":[408777840],"lats":[79824672]}' localhost:3000/ge
