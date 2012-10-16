package com.dbjtech.push.actions;

import org.apache.log4j.Logger;

import org.apache.commons.lang.math.RandomUtils;
import org.apache.struts2.convention.annotation.Action;
import org.apache.struts2.convention.annotation.ParentPackage;
import org.apache.struts2.convention.annotation.Result;
import org.apache.struts2.convention.annotation.Results;
import org.apache.struts2.json.annotations.JSON;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;

import com.dbjtech.push.adaptor.OpenfireAdaptor;
import com.dbjtech.push.db.dao.DPUserDao;
import com.dbjtech.push.db.entities.DPUser;
import com.dbjtech.push.utils.MD5Util;
import com.opensymphony.xwork2.ActionSupport;

@ParentPackage("json-default")
@Results( { @Result(name = "success", type = "json") })
@Controller
public class AccountAction extends ActionSupport {

	public static Logger logger = Logger.getLogger(AccountAction.class
			.getName());
	private static final long serialVersionUID = -5006075558570415924L;

	@Autowired
	private DPUserDao dPUserDao;

	private int status = 0;
	private String message = "Registrate success!";
	// NOTE: here, use a default key
	private String key = "e11e7e3e21180fd";
	private String uid = "";

	@Action(value = "accountCreate")
	public String create() {
		DPUser user = dPUserDao.findFirstByProperty("username", uid);
		logger.info("[PUSH] create account request: user: "+uid );
		if (user != null) {
			status = 1;
			message = "Has been registered!";
			key = user.getPassword();
		} else {
			// key = MD5Util.getMD5(
			// String.valueOf(System.currentTimeMillis())
			// + String.valueOf(RandomUtils
			// .nextInt(Integer.MAX_VALUE))).substring(0,
			// 10);
			if (OpenfireAdaptor.createAccount(uid, key)) {
				user = new DPUser();
				user.setUsername(uid);
				user.setPassword(key);

				dPUserDao.save(user);
			} else {
				status = 2;
				message = "Registrate failed!";
				key = "";
			}
		}
		logger.info("[PUSH] create account response: user: "+uid +", message: "+message);
		return SUCCESS;
	}

	public int getStatus() {
		return status;
	}

	public void setStatus(int status) {
		this.status = status;
	}

	public String getMessage() {
		return message;
	}

	public void setMessage(String message) {
		this.message = message;
	}

	public String getKey() {
		return key;
	}

	public void setKey(String key) {
		this.key = key;
	}

	@JSON(serialize = false)
	public String getUid() {
		return uid;
	}

	public void setUid(String uid) {
		this.uid = uid;
	}

}
