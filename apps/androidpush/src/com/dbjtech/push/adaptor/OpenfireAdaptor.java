package com.dbjtech.push.adaptor;

import java.io.IOException;
import java.util.Properties;

import org.jivesoftware.smack.AccountManager;
import org.jivesoftware.smack.Connection;
import org.jivesoftware.smack.ConnectionConfiguration;
import org.jivesoftware.smack.SmackConfiguration;
import org.jivesoftware.smack.XMPPConnection;
import org.jivesoftware.smack.XMPPException;
import org.springframework.core.io.support.PropertiesLoaderUtils;

public class OpenfireAdaptor {
	
	private static final String HOST = "OpenfireHost";
	private static final String PORT = "OpenfirePort";

	public static Connection getConnection() {
		Properties properties = null;
		try {
			properties = PropertiesLoaderUtils
					.loadAllProperties("config.properties");
		} catch (IOException e) {
			e.printStackTrace();
			return null;
		}

		SmackConfiguration.setLocalSocks5ProxyPort(-1);
		ConnectionConfiguration config = null;
		try {
			config = new ConnectionConfiguration(properties.getProperty(HOST),
					Integer.parseInt(properties.getProperty(PORT)));
			config.setRosterLoadedAtLogin(false);
		} catch (Exception e) {
			e.printStackTrace();
		}
		return new XMPPConnection(config);
	}

	public static boolean changePassword(String account, String oldPassword,
			String newPassword) {
		Connection conn = getConnection();
		try {
			conn.connect();
			conn.login(account, oldPassword);
			AccountManager am = conn.getAccountManager();
			am.changePassword(newPassword);
			return true;
		} catch (XMPPException e) {
			e.printStackTrace();
		} finally {
			conn.disconnect();
		}
		return false;
	}

	public static boolean deleteAccount(String account, String password) {
		Connection conn = getConnection();
		try {
			conn.connect();
			conn.login(account, password);
			AccountManager am = conn.getAccountManager();
			am.deleteAccount();
			return true;
		} catch (XMPPException e) {
			e.printStackTrace();
		} finally {
			conn.disconnect();
		}
		return false;
	}

	public static boolean createAccount(String account, String password) {
		Connection conn = getConnection();
		try {
			conn.connect();
			AccountManager am = new AccountManager(conn);
			am.createAccount(account, password);
			return true;
		} catch (XMPPException e) {
			e.printStackTrace();
		} finally {
			conn.disconnect();
		}
		return false;
	}
}
