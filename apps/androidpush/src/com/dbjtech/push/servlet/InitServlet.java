package com.dbjtech.push.servlet;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;

import org.apache.log4j.Logger;
import org.springframework.context.ApplicationContext;
import org.springframework.web.context.support.WebApplicationContextUtils;

import com.dbjtech.push.actions.AccountAction;
import com.dbjtech.push.adaptor.OpenfireAdaptor;
import com.dbjtech.push.db.dao.DPUserDao;
import com.dbjtech.push.db.entities.DPUser;

import org.springframework.core.io.support.PropertiesLoaderUtils;

import java.io.IOException;
import java.util.Properties;

public class InitServlet extends HttpServlet {

	private DPUserDao dPUserDao;

	private static final long serialVersionUID = -1856843934157231285L;

	public static Logger logger = Logger.getLogger(InitServlet.class.getName());

	@Override
	public void init(ServletConfig config) throws ServletException {
		super.init(config);

		Properties properties;
		try {
			properties = PropertiesLoaderUtils
					.loadAllProperties("config.properties");

			ServletContext sc = getServletContext();
			ApplicationContext ac = WebApplicationContextUtils
					.getWebApplicationContext(sc);
			dPUserDao = ac.getBean(DPUserDao.class);

			int count = dPUserDao.countByProperty("username", properties
					.getProperty("Username"));

			if (count == 0) {
				OpenfireAdaptor.createAccount(properties
						.getProperty("Username"), properties
						.getProperty("Password"));

				// DPUser user = new DPUser();
				// user.setUsername(properties.getProperty("Username"));
				// user.setPassword(properties.getProperty("Password"));
				//
				// dPUserDao.saveOrUpdate(user);

			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}
