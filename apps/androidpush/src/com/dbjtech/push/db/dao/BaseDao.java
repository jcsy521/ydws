package com.dbjtech.push.db.dao;

import javax.annotation.Resource;

import org.hibernate.Session;
import org.hibernate.SessionFactory;

public class BaseDao<T extends java.io.Serializable, ID extends java.io.Serializable>
		extends IBaseDaoImpl<T, ID> {

	@Resource(name = "sessionFactory")
	private SessionFactory sessionFactory;

	@Override
	protected Session getSession() {
		return sessionFactory.getCurrentSession();
	}

}
