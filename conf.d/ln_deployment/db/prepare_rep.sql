-- config the mysql
-- 10.64.77.243 db-1
-- 10.64.77.244 db-2

grant replication slave 
on *.*
to 'replication'@'10.64.77.244'
identified by 'replication';

flush privileges;

show master status;
