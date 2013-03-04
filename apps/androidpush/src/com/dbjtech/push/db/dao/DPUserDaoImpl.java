package com.dbjtech.push.db.dao;

import org.springframework.stereotype.Repository;

import com.dbjtech.push.db.entities.DPUser;

@Repository(value = "dPUsernDao")
public class DPUserDaoImpl extends BaseDao<DPUser, Long> implements DPUserDao {

}
