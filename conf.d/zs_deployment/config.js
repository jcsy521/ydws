module.exports = {
	auth:{
		timestamp_offset: 5*60*1000,//allowed timestamp offset of push/register's param t
		secret: '7c2d6047c7ad95f79cdb985e26a92141',//push api secret
		activation_code_secret: '5ZOl5Lus77yM5L2g5piv5YaF6YOo5pyN5Yqh5Yi35paw55qE5ZCX77yf',//activation_code api secret
	},
	redis:{
		host:'192.168.1.205',
		port:6379,
		options:{},
		select:0
	},
	session:{
		timeout: 3600
	},
	web:{
		port: 6412
	},
	db:{
		message_expired_time: 3600,		//seconds of offline msg expried time
		offline_message_size: 10,		//max return count of offline message when websocket connect
		device_expired_time: 7*24*3600,	//remove device older than this time
		// for tingodb
		// type: 'tingodb',
		// path: 'database',

		// for mongodb
		type: 'mongodb',
		path: 'mongodb://127.0.0.1:27017/server?auto_reconnect=true&socketTimeoutMS=600000',

		// for redis
		// type: 'redis',
	},
	apn:{
		cert: "./tools/apn/development_xiaobao_cert.pem",
		key: "./tools/apn/development_xiaobao_key.pem",

		//gateway: 'gateway.sandbox.push.apple.com',
		//port: 2195,
		production: false,
	},
	upload:{
		path: 'upload',
	},
}

