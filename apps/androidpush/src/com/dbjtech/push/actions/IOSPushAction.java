package com.dbjtech.push.actions;

import org.apache.log4j.Logger;
import org.apache.struts2.convention.annotation.Action;
import org.apache.struts2.convention.annotation.ParentPackage;
import org.apache.struts2.convention.annotation.Result;
import org.apache.struts2.convention.annotation.Results;
import org.apache.struts2.json.annotations.JSON;
import org.springframework.stereotype.Controller;

import com.opensymphony.xwork2.ActionSupport;

import javapns.Push;
import javapns.communication.exceptions.CommunicationException;
import javapns.communication.exceptions.KeystoreException;
import javapns.notification.Payload;
import javapns.notification.PushNotificationPayload;
import org.json.JSONException;

@ParentPackage("json-default")
@Results( { @Result(name = "success", type = "json") })
@Controller
public class IOSPushAction extends ActionSupport {
	private static final long serialVersionUID = 4507089270367724545L;
	public static Logger logger = Logger.getLogger(PushAction.class.getName());

	private int status = 0;
	private String uid = "";
	private String alert = "";
	private String language = "";
	private String badge = "";
	private String message = "Send success!";
	private String body = "";
	private String password = "dbjtech";
	private String keystore = "pushkey.p12";
	private String keystore_dev = "pushkey_dev.p12";

	@Override
	@Action(value = "iospush")
	public String execute() {

		logger.info("[IOSPUSH] push request: user: " + uid + " , alert: "
				+ alert + " , language: " + language + " , badge: " + badge
				+ ", body: \n" + body);

		try {
			if (language.equals("zh_CN")) {
				keystore = "pushkey_cn.p12";
				keystore_dev = "pushkey_cn_dev.p12";
				logger.info("[IOSPUSH] use pushkey_cn.p12 ");
			} else if (language.equals("en_US")) {
				keystore = "pushkey_en.p12";
				keystore_dev = "pushkey_en_dev.p12";
				logger.info("[IOSPUSH] use pushkey_en.p12 ");
			} else {
				keystore = "pushkey.p12";
				keystore_dev = "pushkey_dev.p12";
				logger.info("[IOSPUSH] use pushkey.p12 ");
			}

			PushNotificationPayload sendDate = new PushNotificationPayload();
			sendDate.addAlert(alert);
			sendDate.addBadge(Integer.parseInt(badge));
			sendDate.addCustomDictionary("acb", body);

			// NOTE: just test for dev!!! some day, it will be removed.
			pushAlert_test(sendDate, keystore_dev, password, uid);

			pushAlert(sendDate, keystore, password, uid);

		} catch (JSONException e) {
			e.printStackTrace();
			message = "iospush failed!";
		} catch (Exception e) {
			e.printStackTrace();
			message = "iospush failed!";
		}
		logger.info("[IOSPUSH] push response: user: " + uid + ", message: "
				+ message);
		return SUCCESS;
	}

	private static void pushAlert(Payload data, String keystore,
			String password, String uid) {
		try {
			logger.info("[IOSPUSH] push for pro");
			// true: product
			// false: dev
			Push.payload(data, keystore, password, true, uid);
		} catch (CommunicationException e) {
			e.printStackTrace();
		} catch (KeystoreException e) {
			e.printStackTrace();
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	private static void pushAlert_test(Payload data, String keystore,
			String password, String uid) {
		try {
			logger.info("[IOSPUSH] push for dev");
			// true: product
			// false: dev
			Push.payload(data, keystore, password, false, uid);
		} catch (CommunicationException e) {
			e.printStackTrace();
		} catch (KeystoreException e) {
			e.printStackTrace();
		}
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

	@JSON(serialize = false)
	public String getAlert() {
		return alert;
	}

	public void setAlert(String alert) {
		this.alert = alert;
	}

	@JSON(serialize = false)
	public String getLanguage() {
		return language;
	}

	public void setLanguage(String language) {
		this.language = language;
	}

	@JSON(serialize = false)
	public String getBadge() {
		return badge;
	}

	public void setBadge(String badge) {
		this.badge = badge;
	}

}
