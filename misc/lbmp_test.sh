
#!/bin/bash

# subscription
#curl -d '{"sim":"14778471517", "action":"A"}' http://app01:3001/subscription

# le
curl -d '{"sim":"14778477120","lac":"","cid":"","mcc":"","mnc":""}' http://app01:3001/le
