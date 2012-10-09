package com.dbjtech.push.db.dao;

import java.lang.reflect.ParameterizedType;
import java.util.List;

import org.apache.log4j.Logger;
import org.hibernate.Query;
import org.hibernate.Session;

@SuppressWarnings("unchecked")
public abstract class IBaseDaoImpl<T extends java.io.Serializable, ID extends java.io.Serializable>
		implements IBaseDao<T, ID> {
	
	protected static final Logger LOGGER = Logger.getLogger(IBaseDaoImpl.class);

	protected abstract Session getSession();

	private Class<T> persistentClass;

	public Class<T> getPersistentClass() {
		return persistentClass;
	}

	public IBaseDaoImpl() {
		persistentClass = (Class<T>) ((ParameterizedType) getClass()
				.getGenericSuperclass()).getActualTypeArguments()[0];

	}

	public int countAll() {
		String queryString = "select count(*) from "
				+ getPersistentClass().getName();
		Query query = this.getSession().createQuery(queryString);
		List<?> list = query.list();
		Long result = (Long) list.get(0);
		return result.intValue();
	}

	public int countByProperty(String propertyName, Object value) {
		String[] propertyNames = new String[] { propertyName };
		Object[] values = new Object[] { value };
		return this.countByPropertys(propertyNames, values);
	}

	public int countByPropertys(String[] propertyNames, Object[] values) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("select count(*) from "
				+ getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}

		String queryString = strBuffer.toString();
		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}

		List<?> list = query.list();
		Long result = (Long) list.get(0);
		return result.intValue();
	}

	public T findById(ID id) {
		return (T) this.getSession().get(getPersistentClass(), id);
	}

	public void save(T entity) {
		this.getSession().save(entity);
	}

	public void saveOrUpdate(T entity) {
		this.getSession().saveOrUpdate(entity);
	}

	public void update(T entity) {
		this.getSession().update(entity);
	}

	public void delete(T entity) {
		this.getSession().delete(entity);
	}

	public void deleteByProperty(String propertyName, Object value) {
		String[] propertyNames = new String[] { propertyName };
		Object[] values = new Object[] { value };
		deleteByPropertys(propertyNames, values);
	}

	public void deleteByPropertys(String[] propertyNames, Object[] values) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("delete from " + getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}

		String queryString = strBuffer.toString();
		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}
		query.executeUpdate();
	}

	public List<T> findAll() {
		String queryString = "from " + getPersistentClass().getName();
		Query query = this.getSession().createQuery(queryString);
		return query.list();
	}

	public List<T> findAll(int page, int pageSize) {
		String queryString = "from " + getPersistentClass().getName();
		Query query = this.getSession().createQuery(queryString);
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public List<T> findAll(String orderBy) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model order by model." + orderBy;
		Query query = this.getSession().createQuery(queryString);
		return query.list();
	}

	public List<T> findAll(int page, int pageSize, String orderBy) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model order by model." + orderBy;
		Query query = this.getSession().createQuery(queryString);
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public List<T> findByProperty(String propertyName, Object value) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model where model." + propertyName + "= ? ";
		Query query = this.getSession().createQuery(queryString);
		query.setParameter(0, value);
		return query.list();
	}

	public List<T> findByProperty(String propertyName, Object value,
			String orderBy) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model where model." + propertyName + "= ? "
				+ " order by model." + orderBy;
		Query query = this.getSession().createQuery(queryString);
		query.setParameter(0, value);
		return query.list();
	}

	public List<T> findByProperty(String propertyName, Object value, int page,
			int pageSize) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model where model." + propertyName + "= ? ";
		Query query = this.getSession().createQuery(queryString);
		query.setParameter(0, value);
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public List<T> findByProperty(String propertyName, Object value,
			String orderBy, int page, int pageSize) {
		String queryString = "from " + getPersistentClass().getName()
				+ " as model where model." + propertyName + "= ? "
				+ " order by model." + orderBy;
		Query query = this.getSession().createQuery(queryString);
		query.setParameter(0, value);
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public List<T> findByPropertys(String[] propertyNames, Object[] values) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("from " + getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}
		String queryString = strBuffer.toString();

		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}

		return query.list();
	}

	public List<T> findByPropertys(String[] propertyNames, Object[] values,
			String orderBy) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("from " + getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}
		strBuffer.append(" order by model." + orderBy);
		String queryString = strBuffer.toString();

		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}
		return query.list();
	}

	public List<T> findByPropertys(String[] propertyNames, Object[] values,
			int page, int pageSize) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("from " + getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}

		String queryString = strBuffer.toString();
		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public List<T> findByPropertys(String[] propertyNames, Object[] values,
			String orderBy, int page, int pageSize) {
		StringBuffer strBuffer = new StringBuffer();
		strBuffer.append("from " + getPersistentClass().getName());
		strBuffer.append(" as model where ");
		for (int i = 0; i < propertyNames.length; i++) {
			if (i != 0)
				strBuffer.append(" and");
			strBuffer.append(" model.");
			strBuffer.append(propertyNames[i]);
			strBuffer.append("=");
			strBuffer.append("? ");
		}

		strBuffer.append(" order by model." + orderBy);
		String queryString = strBuffer.toString();
		Query query = this.getSession().createQuery(queryString);
		for (int i = 0; i < values.length; i++) {
			query.setParameter(i, values[i]);
		}
		int firstResult = (page * pageSize);
		query.setFirstResult(firstResult);
		query.setMaxResults(pageSize);
		return query.list();
	}

	public T findFirst() {
		List<T> list = findAll(0, 1);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

	public T findFirst(String orderBy) {
		List<T> list = findAll(0, 1, orderBy);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

	public T findFirstByProperty(String propertyName, Object value) {
		List<T> list = findByProperty(propertyName, value);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

	public T findFirstByProperty(String propertyName, Object value,
			String orderBy) {
		List<T> list = findByProperty(propertyName, value, orderBy, 0, 1);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

	public T findFirstByPropertys(String[] propertyNames, Object[] values) {
		List<T> list = findByPropertys(propertyNames, values, 0, 1);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

	public T findFirstByPropertys(String[] propertyNames, Object[] values,
			String orderBy) {
		List<T> list = findByPropertys(propertyNames, values, orderBy, 0, 1);
		if (list != null && list.size() > 0) {
			return list.get(0);
		}

		return null;
	}

}
