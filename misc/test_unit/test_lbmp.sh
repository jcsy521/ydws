
#!/bin/bash

# subscription
#curl -d '{"sim":"14778477173", "action":"A"}' http://app01:3001/subscription

# le
#curl -d '{"sim":"14778742471","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le
#curl -d '{"sim":"14778477173","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le

# ge
curl -i -X POST  -d '{"lons":[408438648],"lats":[81136656]}' localhost:3000/ge
#curl -i -X POST  -d '{"lons":[408438648],"lats":[81136656]}' localhost:3000/ge

# gv 
#curl -i -X POST  -d '{"lat":22.367554722222224,"lon":113.44926111111111}' localhost:3000/gv
