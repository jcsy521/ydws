package com.dbjtech.push.actions;

import org.apache.log4j.Logger;
import org.apache.struts2.convention.annotation.Action;
import org.apache.struts2.convention.annotation.ParentPackage;
import org.apache.struts2.convention.annotation.Result;
import org.apache.struts2.convention.annotation.Results;
import org.apache.struts2.json.annotations.JSON;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;

import com.dbjtech.push.Pusher;
import com.dbjtech.push.db.dao.DPUserDao;
import com.dbjtech.push.db.entities.DPUser;
import com.opensymphony.xwork2.ActionSupport;

@ParentPackage("json-default")
@Results({ @Result(name = "success", type = "json") })
@Controller
public class PushAction extends ActionSupport {
	private static final long serialVersionUID = 4507089270367724545L;
	public static Logger logger = Logger.getLogger(PushAction.class
			.getName());
	
	@Autowired
	private Pusher pusher;

	@Autowired
	private DPUserDao dPUserDao;

	private int status = 0;
	private String uid = "";
	private String key = "";
	private String message = "Send success!";
	private String body = "";

	@Override
	@Action(value = "push")
	public String execute() {
		DPUser user = dPUserDao.findFirstByProperty("username", uid);
		logger.info("[PUSH] push request: user: "+uid +", content: \n"+body);
		if (user == null) {
			status = 1;
			message = "uid does not exist!";
		} else if (!user.getPassword().equals(key)) {
			status = 2;
			message = "Key is error!";
		} else {
			pusher.sentMessage(uid, body);
		}
		logger.info("[PUSH] push response: user: "+uid +", message: "+message);
		return SUCCESS;
	}

	public int getStatus() {
		return status;
	}

	public void setStatus(int status) {
		this.status = status;
	}

	@JSON(serialize = false)
	public String getUid() {
		return uid;
	}

	public void setUid(String uid) {
		this.uid = uid;
	}

	@JSON(serialize = false)
	public String getKey() {
		return key;
	}

	public void setKey(String key) {
		this.key = key;
	}

	public String getMessage() {
		return message;
	}

	public void setMessage(String message) {
		this.message = message;
	}

	@JSON(serialize = false)
	public String getBody() {
		return body;
	}

	public void setBody(String body) {
		this.body = body;
	}

}
