/*
* 通知管理
*/
/*
* 通知新增
*/
window.dlf.fn_notifyManage_addInit = function() {
	dlf.fn_dialogPosition('notifyManageAdd');	// 设置dialog的位置并显示
	dlf.fn_unLockScreen(); // 添加页面遮罩
	dlf.fn_setItemMouseStatus($('#notifyManageSave'), 'default', 'fs0');
	// 初始化数据
	$('#text_notifyManageMsg').val('').unbind('keyup').keyup(function(e) {
		dlf.fn_setItemMouseStatus($('#notifyManageSave'), 'pointer', new Array('fs', 'fs2'));
	});
	
}


/*
*保存通知并发送通知
*/ 
window.dlf.fn_notifyManageMsg = function() {
	var str_message = $.trim($('#text_notifyManageMsg').val()),
		n_msgLength = (str_message.replace(/[^\x00-\xff]/g, '^^')).length, 
		arr_tMobiles = [],
		n_pMoblesLen = 0,
		obj_notifyManageData = {'content': str_message, 'mobiles': []},
		str_saveBtnCursor = $('#notifyManageSave').css('cursor');
	
	if ( str_saveBtnCursor == 'default' ) {
		return;
	}
	
	// 输入内容256个汉字
	if ( str_message == '' ) {
		dlf.fn_jNotifyMessage('请输入通知内容！', 'message', false, 4000); 
		return;
	} else if ( n_msgLength > 512 ) {
		dlf.fn_jNotifyMessage('消息内容最大长度是256个汉字！', 'message', false, 4000); 
		return;
	}
	
	//获取终端信息MOBILE
	$('.j_leafNode').each(function(leafEvent) { 
		var str_tempLeafClass = $(this).attr('class'), 
			str_tempLeafMobile = $(this).children('a').attr('title');
		
		if ( str_tempLeafClass.search('jstree-checked') != -1) {
			arr_tMobiles.push(str_tempLeafMobile);
		}
	});
	obj_notifyManageData.mobiles = arr_tMobiles;
	n_pMoblesLen = arr_tMobiles.length;
	if ( n_pMoblesLen <= 0 ){
		dlf.fn_jNotifyMessage('请选择通知接收号码！', 'message', false, 4000); 
		return;
	}
	dlf.fn_jsonPost(NOTIFYMANAGE_ADD_URL, obj_notifyManageData, 'notifyManage', '通知发送中');
}
/*
* 通知删除
*/
window.dlf.fn_deleteNotifys = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该通知吗？') ) {
			$.delete_(NOTIFYMANAGE_ADD_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					$('#notifyManageSearchTable tr[id='+ n_id +']').remove();
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			});
		}
	}
}