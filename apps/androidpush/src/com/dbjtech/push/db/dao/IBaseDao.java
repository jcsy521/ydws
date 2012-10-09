package com.dbjtech.push.db.dao;

import java.io.Serializable;
import java.util.List;

public abstract interface IBaseDao<T, ID extends Serializable> {
	public abstract Class<T> getPersistentClass();
	
	public abstract int countAll();
	public abstract int countByProperty(String propertyName, Object value);
	public abstract int countByPropertys(String[] propertyNames, Object[] values);
	
	public abstract T findById(ID id);
	
	public abstract void save(T entity);
	public abstract void saveOrUpdate(T entity);
	public abstract void update(T entity);
	
	public abstract void delete(T entity);
	public abstract void deleteByProperty(String propertyName, Object value);
	public abstract void deleteByPropertys(String[] propertyNames,
			Object[] values);
	
	public abstract List<T> findAll();
	public abstract List<T> findAll(int page, int pageSize);
	public abstract List<T> findAll(String orderBy);
	public abstract List<T> findAll(int page, int pageSize, String orderBy);

	public abstract List<T> findByProperty(String propertyName, Object value);
	public abstract List<T> findByProperty(String propertyName, Object value, String orderBy);
	public abstract List<T> findByProperty(String propertyName, Object value, int page,
			int pageSize);
	public abstract List<T> findByProperty(String propertyName, Object value, String orderBy, int page,
			int pageSize);
	
	public abstract List<T> findByPropertys(String[] propertyNames,
			Object[] values);
	public abstract List<T> findByPropertys(String[] propertyNames,
			Object[] values, String orderBy);
	public abstract List<T> findByPropertys(String[] propertyNames, Object[] values, 
			int page, int pageSize);
	public abstract List<T> findByPropertys(String[] propertyNames, Object[] values, String orderBy,
			int page, int pageSize);
	
	public abstract T findFirst();
	public abstract T findFirst(String orderBy);
	
	public abstract T findFirstByProperty(String propertyName, Object value);
	public abstract T findFirstByProperty(String propertyName, Object value, String orderBy);
	
	public abstract T findFirstByPropertys(String[] propertyNames,
			Object[] values);
	public abstract T findFirstByPropertys(String[] propertyNames,
			Object[] values, String orderBy);
}
