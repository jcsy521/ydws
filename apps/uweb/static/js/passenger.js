/*
* 乘客管理相关操作方法
* 咨询推送逻辑
*/
// 乘客保存
dlf.fn_savePassenger = function() {
	var	str_id = $('#hidPassengerId').val(),
		str_name = $('#txt_passengerName').val(),
		str_mobile = $('#txt_passengerMobile').val(),
		obj_header = $('#passengerTableHeader'),
		b_addPassengerHeader = obj_header.is(':hidden'),
		obj_passengerData = {'id': '', 'name': str_name, 'mobile': str_mobile};
	
	if ( b_addPassengerHeader ) {	// 判断表头是否显示
		obj_header.show();
	}
	if ( str_id ) {
		obj_passengerData.id = parseInt(str_id);
		dlf.fn_jsonPut(PASSENGER_URL, obj_passengerData, 'passenger', '乘客数据保存中');
	} else {
		dlf.fn_jsonPost(PASSENGER_URL, obj_passengerData, 'passenger', '乘客数据保存中');
	}
}
/**
* 编辑乘客
*/
dlf.fn_editPassenger = function(n_id) {
	dlf.fn_onInputBlur();	// 乘客手机号事件侦听
	$('#addPassengerForm input').css('color', '#000000');
	if ( n_id ) {
			var obj_currentPassengerItem = $('#passengerTable tr[id='+ n_id +']'), 
				obj_currentPassengerItemTds = obj_currentPassengerItem.children(), 
				str_currentName = $(obj_currentPassengerItemTds.eq(0)).html(),
				str_currentMobile = $(obj_currentPassengerItemTds.eq(1)).html();
			
			$('#hidPassengerId').val(n_id);
			$('#txt_passengerName').val(str_currentName);
			$('#txt_passengerMobile').val(str_currentMobile).data('oldmobile', str_currentMobile);
			
		$('#addPassengerDialog').dialog('open').attr('title', '编辑乘客').dialog('option', 'title', '编辑乘客');
	}
}

/**
* 删除乘客
*/
dlf.fn_deletePassenger = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该乘客吗？') ) {
			$.delete_(PASSENGER_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					$('#passengerTable tr[id='+ n_id +']').remove();
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	}
}
/*
*================================================push info start=====================================
*咨询操作的的相关方法
*/
// 咨询推送初始化
dlf.fn_initInfoPush = function() { // todo 页面优化
	var str_infoPush = 'infoPush';
	
	dlf.fn_dialogPosition(str_infoPush);	// 设置dialog的位置并显示
	dlf.fn_unLockScreen(); // 添加页面遮罩
	dlf.fn_setItemMouseStatus($('#infoPushSave'), 'pointer', new Array('fs', 'fs2'));	// 保存按钮鼠标滑过样式
	// 初始化数据
	$('#text_infoPush').val('');
	$('#infoPush_smsWay, #infoPush_pushWay').removeAttr('checked');
	obj_infoPushChecks = {};
	//获取乘客数据 
	dlf.fn_setSearchRecord(str_infoPush);
	dlf.fn_searchData(str_infoPush);
	$('#infoPush_allChecked').unbind('click').click(function(event) {
		var str_isCheck = $(this).attr('checked'), 
			obj_allChecks = $('.j_infoPushChecks :checkbox[name="infoPush_check"]');
		
		if ( str_isCheck ) {
			obj_allChecks.attr('checked', 'checked');
			// 将所有的pid保存
			obj_allChecks.each(function() {
				var str_checkPid = $(this).val(), 
					str_userid = $(this).attr('userid');
				
				obj_infoPushChecks[str_userid] = str_checkPid;
			});
		} else {
			obj_allChecks.removeAttr('checked');
			obj_infoPushChecks = {};
		}
	}).removeAttr('checked');
}
/*保存消息并发送消息*/ 
dlf.fn_saveInfoPush = function() {
	// 拿到所有选中的乘客的pid
	var str_message = $('#text_infoPush').val(),
		b_allChecked = $('#infoPush_allChecked').attr('checked'), 
		b_smsWayChecked = $('#infoPush_smsWay').attr('checked') == 'checked' ? 1 : 0, 
		b_pushWayChecked = $('#infoPush_pushWay').attr('checked') == 'checked' ? 1 : 0, 
		arr_pids = [],
		arr_mobiles = [], 
		n_pids = 0, 
		obj_infoPushData = {'message': str_message, 'pids': null, 'mobiles': null, 'all_passenger': 0 , 'sms_way': b_smsWayChecked, 'push_way': b_pushWayChecked};
	
	//获取乘客信息	
	if ( b_allChecked ) { // 如果已全选
		obj_infoPushData.all_passenger = 1;
	} else {	
		// 取PID
		for( var obj_tempCheck in obj_infoPushChecks ) {
			var str_checkPid = obj_infoPushChecks[obj_tempCheck];
			
			if ( str_checkPid || str_checkPid == '' ) { 
				arr_pids.push(str_checkPid);
			}
		}
		// 取MOBILE
		for( var obj_tempMobile in obj_infoPushMobiles ) {
			var str_mobile = obj_infoPushMobiles[obj_tempMobile];
			
			if ( str_mobile || str_mobile == '' ) { 
				arr_mobiles.push(str_mobile);
			}
		}
		obj_infoPushData.pids = arr_pids;
		obj_infoPushData.mobiles = arr_mobiles;
		n_pids = arr_pids.length;
		
		if ( n_pids <= 0 ) {
			dlf.fn_jNotifyMessage('您选的个数不对（至少选一个）。', 'message', false, 3000);
			return;
		}
	}
	// 获取消息发送方式
	if ( b_smsWayChecked == 0 && b_pushWayChecked == 0 ) {
		dlf.fn_jNotifyMessage('请您选择消息发送方式（至少选一种）。', 'message', false, 3000);
		return;
	}
	dlf.fn_jsonPost(PUSHINFO_URL, obj_infoPushData, 'infoPush', '消息发送中');
}