
#!/bin/bash

# subscription
curl -d '{"sim":"15919100992", "action":"A"}' http://app01:3001/subscription

# le
curl -d '{"sim":"15919100992","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le
#curl -d '{"sim":"14778477173","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le

# ge
#curl -i -X POST  -d '{"lons":[408845556],"lats":[80550504]}' localhost:3001/ge
#curl -i -X POST  -d '{"lons":[408777840],"lats":[79824672]}' localhost:3000/ge
