package com.dbjtech.push;

import java.io.IOException;
import java.io.Serializable;

import org.jivesoftware.smack.Chat;
import org.jivesoftware.smack.ChatManager;
import org.jivesoftware.smack.Connection;
import org.jivesoftware.smack.XMPPException;
import org.springframework.stereotype.Repository;
import org.springframework.core.io.support.PropertiesLoaderUtils;
import java.util.Properties;

import com.dbjtech.push.adaptor.OpenfireAdaptor;

@Repository
public class Pusher implements Serializable {

	private static final long serialVersionUID = 5835100304400071979L;
	private Connection con;

	public Pusher() {
		con = OpenfireAdaptor.getConnection();
	}

	public void sentMessage(String uid, String message) {
		/**
		 * Push message to openfire.
		 */		
		
		try {
			Properties properties = PropertiesLoaderUtils
			.loadAllProperties("config.properties");
			
			if (!con.isConnected()) {
				con.connect();
			}

			if (!con.isAuthenticated()) {
				con.login(properties.getProperty("Username"), properties.getProperty("Password"));
			}

			ChatManager chatManager = con.getChatManager();

			Chat chat = chatManager.createChat(uid + "@" + properties.getProperty("OpenfireServer"), null);
			chat.sendMessage(message);
		} catch (IOException e1) {
			e1.printStackTrace();
		} catch (XMPPException e) {
			e.printStackTrace();
		}
	}
}
