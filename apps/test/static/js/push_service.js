var dlf = {};


$(function() {

	var socketCon = null;

	//对相应终端进行追踪操作
	dlf.fn_initPushServices = function() {
		var str_pushId = $('#pushId').html(),
			str_pushKey = $('#pushkey').html(),
			str_basePushUrl = 'http://push.pinganbb.info:80',
			str_pushUrl = '';

		// 获取dev_id		
		str_devid = new Date().getTime();
		str_pushUrl = 'packet_type=C1&from=0&push_id=' + str_pushId + '&psd=' + str_pushKey + '&devid=' + str_devid;

		socketCon = io.connect(str_basePushUrl, {
			'query': str_pushUrl,
			'force new connection': true
		});

		//侦听服务
		socketCon.on('api/resp', function(data) {

			var obj_pushData = data,
				str_packetType = ''; //obj_pushData.packet_type;

			if (typeof(obj_pushData) == 'string') {
				obj_pushData = JSON.parse(data);
			}
			str_packetType = obj_pushData.packet_type;

			console.log('push log:   ', new Date(), typeof(obj_pushData), str_packetType, obj_pushData);
			$('#pushlog').append('<div>pushlog: IN  dayType:' + typeof(obj_pushData) + '</div>');
			fn_pushCallback({
				'packet_type': 'C7',
				'status': 0,
				'msg': 'SUCCESS'
			});
		});

		//侦听连接失败
		socketCon.on('error', function(event) {
			$('#pushlog').append('<div>pushlog: ERROR  ' + event + '</div>');
			//socketCon.disconnect();
			if (event != 'handshake unauthorized') {
				socketCon.disconnect();
			}
			setTimeout(function(e) {
				//fn_reRequestPush();
			}, 1000 * 3);
		});
		//连接被断开时
		socketCon.on('connect', function(event) {
			//console.log('push connect:  ',event);
			$('#pushlog').append('<div>pushlog: push connect</div>');
		});
	}

	//重新请求push信息
	function fn_reRequestPush() {
			$.ajax({
				type: 'get',
				url: 'http://test.ichebao.net/testwspush?uid=' + $('#uid').val(),

				data: '',
				dataType: 'json',
				cache: false,
				contentType: 'application/json; charset=utf-8',
				complete: function(data) {
					console.log("complete    ", data);
				},
				success: function(data) {
					console.log("success    ", data);
					if (data.status == 0) {
						var obj_pushData = data.wspush;

						$('#pushkey').html(obj_pushData.key);
						$('#pushId').html(obj_pushData.id);

						dlf.fn_initPushServices();
					} else if (data.status == 403 || data.status == 24) {
						window.location.replace('/');
					}
				},
				error: function(XMLHttpRequest) {
					console.log("failed     ", XMLHttpRequest);
					return;
				}
			});
		}
		//响应push
	function fn_pushCallback(obj_pushCallbackData) {
		console.log("C:     ", new Date(), obj_pushCallbackData)
		$('#pushlog').append('<div>pushlog: OUT </div>');
		socketCon.emit('api/resp', obj_pushCallbackData);
	}

	// invoke the method.
	//dlf.fn_initPushServices();
	$('#linkpush').unbind('click').click(fn_reRequestPush);
});