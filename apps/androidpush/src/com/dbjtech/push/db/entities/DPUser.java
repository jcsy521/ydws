package com.dbjtech.push.db.entities;

import java.io.Serializable;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import static javax.persistence.GenerationType.IDENTITY;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "ofUser", catalog = "DB_PUSH")
public class DPUser implements Serializable {

	private static final long serialVersionUID = -6926563242626663113L;

	private String username;
	private String password;
	private String plainPassword;
	private String encryptedPassword;
	private String name;
	private String email;
	private String creationDate;
	private String modificationDate;

	@Id
	@GeneratedValue(strategy = IDENTITY)
	@Column(name = "username", unique = true, nullable = false)
	public String getUsername() {
		return this.username;
	}

	public void setUsername(String username) {
		this.username = username;
	}


	public void setPassword(String password) {
		this.password = password;
	}
	
	@Column(name = "password")
	public String getPassword() {
		return this.password;
	}


	public void setPlainPassword(String plainPassword) {
		this.plainPassword = plainPassword;
	}
	
	@Column(name = "plainPassword")
	public String getPlainPassword() {
		return plainPassword;
	}
	
	public void setEncryptedPassword(String encryptedPassword) {
		this.encryptedPassword = encryptedPassword;
	}

	@Column(name = "encryptedPassword")
	public String getEncryptedPassword() {
		return encryptedPassword;
	}

	
	public void setName(String name) {
		this.name = name;
	}
	
	@Column(name = "name")
	public String getName() {
		return name;
	}

	public void setEmail(String email) {
		this.email = email;
	}
	
	@Column(name = "email")
	public String getEmail() {
		return email;
	}
	
	public void setCreationDate(String creationDate) {
		this.creationDate = creationDate;
	}
	
	@Column(name = "creationDate")
	public String getCreationDate() {
		return creationDate;
	}
	
	public void setModificationDate(String modificationDate) {
		this.modificationDate = modificationDate;
	}
	
	@Column(name = "modificationDate")
	public String getModificationDate() {
		return modificationDate;
	}

}
