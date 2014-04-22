/**
* 安捷通白名单相关操作
*/
$(function () {
	
	// 设置标题头样式
	$('#search_table th').addClass('ui-state-default');
	
	// 查询号码是否在白名单中事件侦听 
	$('#whitelist_search').click(function(e) {
		fn_validCookie();
		
		var str_mobile = $('#mobile').val(), 
			obj_conditionData = {'mobile': str_mobile},
			obj_whitelistBody = $('#whitelist_tbody');
		
		obj_whitelistBody.html('');
		
		if ( !fn_validMobile(str_mobile) ) {
			return;
		}
		
		$.post('/whitelist_ajt/search',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.status == 0 ) {
				var str_tbodyText ='<tr>',
					obj_tempData = data.res,
					str_mobile = obj_tempData.mobile;
				
				str_tbodyText += '<td class="sorting_1">'+str_mobile+'</td>';
				str_tbodyText += '<td class="sorting_1">'+toHumanDate(obj_tempData.timestamp, 'yes')+'</td>';
				
				obj_whitelistBody.html(str_tbodyText);
			} else {
				alert(data.message);
			}
		});
	});
	// 新增初始化dialog
	$('#addWhitelistDialog').dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	// 将号码加入白名单中事件侦听 
	$('#whitelist_add').click(function(e) { 
		if ( fn_validCookie() ) {
			return;
		}
		
		$('#txt_whitelistMobile').val('');
		$('#addWhitelistDialog').attr('title', '新增白名单号码').dialog('option', 'title', '新增白名单号码').dialog( "open" );
		
	});
	// 保存白名单事件
	$('#addWhitelistSave').click(function(e) {
		if ( fn_validCookie() ) {
			return;
		}
	
		var str_mobile = $('#txt_whitelistMobile').val(), 
			obj_conditionData = {'mobile': str_mobile};
			
		if ( !fn_validMobile(str_mobile) ) {
			return;
		}
		
		$.post('/whitelist_ajt',  JSON.stringify(obj_conditionData), function (data) {
			alert(data.message);
			if ( data.status == 0 ) {
				$('#addWhitelistDialog').dialog('close');
			}
		});
		
	});
		
	//批量导入白名单初始化
	$('#fileUploadWrapper').dialog({
		autoOpen: false,
		height: 554,
		width: 630,
		position: [300, 100],
		modal: true,
		resizable: false
	});	
		
	//批量导入白名单点击
	$('#whitelist_addbatch').click(function(e) {
		if ( fn_validCookie() ) {
			return;
		}
		var obj_upfile = window.frames['fileUploadIframe'].document.getElementById('fileUploadTable'),
			obj_msg = window.frames['fileUploadIframe'].document.getElementById('jNotifyMessage');
			
		$(obj_upfile).remove().html('');
		$(obj_msg).html('');
		$('#fileUploadIframe').attr('src', '/whitelist_ajt/batch/import');
		$('#fileUploadWrapper').attr('title', '批量导入白名单号码').dialog('option', 'title', '批量导入白名单号码').dialog( "open" );
	});
	
	fn_unLockScreen();
});

/*
* 验证手机号是否合法
*/
function fn_validMobile(str_mobile, str_msgTitle) {
	var MOBILEREG =  /^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/,
		str_alertMsg = '终端';
		
	if ( fn_validCookie() ) {
		return;
	}
	
	if ( str_msgTitle ) {
		str_alertMsg = str_msgTitle;
	}
	if ( str_mobile == '' ) {
		alert('请输入'+ str_alertMsg +'手机号！');
		return false;
	}
	
	if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
		alert('您输入的'+ str_alertMsg +'手机号不合法，请重新输入！');
		return false;
	}
	return true;
}


// 验证cookie是否超时
function fn_validCookie() {
	if(!$.cookie('ACBADMIN')) {
		alert('本次登陆已经超时，系统将重新进入登陆页面。');
		parent.window.location.replace('/login'); // redirect to the index.
		return true;
	}
	return false;
}
