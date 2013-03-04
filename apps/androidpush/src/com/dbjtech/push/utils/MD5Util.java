package com.dbjtech.push.utils;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import org.apache.log4j.Logger;

public class MD5Util {
	private static Logger logger = Logger.getLogger(MD5Util.class);

	static char hexDigits[] = { '0', '1', '2', '3', '4', '5', '6', '7', '8',
			'9', 'a', 'b', 'c', 'd', 'e', 'f' };

	public static String getFileMD5(InputStream fis) {
		MessageDigest md = null;
		try {
			md = MessageDigest.getInstance("MD5");
		} catch (NoSuchAlgorithmException e) {
			e.printStackTrace();
		}

		byte[] buffer = new byte[2048];
		int length = -1;
		long s = System.currentTimeMillis();
		try {
			while ((length = fis.read(buffer)) != -1) {
				md.update(buffer, 0, length);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} finally {
			try {
				fis.close();
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		}
		System.err.println("last: " + (System.currentTimeMillis() - s));
		byte[] b = md.digest();
		return byteToHexStringSingle(b);
	}

	public static String getFileMD5(File file) {
		try {
			return getFileMD5(new FileInputStream(file));
		} catch (FileNotFoundException e) {
			logger.error(e.getMessage());
		}
		return null;
	}

	public static String getMD5(String message) {
		try {
			MessageDigest md = MessageDigest.getInstance("MD5");
			byte[] b = md.digest(message.getBytes("utf-8"));
			return byteToHexStringSingle(b);// byteToHexString(b);
		} catch (NoSuchAlgorithmException e) {
			e.printStackTrace();
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
		return null;
	}

	public static String byteToHexStringSingle(byte[] byteArray) {
		StringBuffer md5StrBuff = new StringBuffer();

		for (int i = 0; i < byteArray.length; i++) {
			if (Integer.toHexString(0xFF & byteArray[i]).length() == 1)
				md5StrBuff.append("0").append(
						Integer.toHexString(0xFF & byteArray[i]));
			else
				md5StrBuff.append(Integer.toHexString(0xFF & byteArray[i]));
		}

		return md5StrBuff.toString();
	}

}
