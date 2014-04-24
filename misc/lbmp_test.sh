
#!/bin/bash

# subscription
curl -d '{"sim":"13011292221", "action":"A"}' http://app01:3001/subscription

# le
#curl -d '{"sim":"14778477120","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le

# ge
#curl -i -X POST  -d '{"lons":[408777840],"lats":[79824672]}' localhost:3000/ge
