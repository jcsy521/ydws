/**
* 白名单相关操作
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
		
		$.post('/whitelist_search',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.success == 0 ) {
				var str_tbodyText ='<tr>',
					obj_tempData = data.whitelist,
					str_mobile = obj_tempData.mobile,
					str_bizType = obj_tempData.biz_type,
					str_planName = '20元(汽车)';
				
				if ( str_bizType == 0 ) {
					str_planName = '10元(电动车)';
				}
				str_tbodyText += '<td class="sorting_1">'+str_mobile+'</td>';
				str_tbodyText += '<td class="sorting_1">'+str_planName+'</td>';
				str_tbodyText += '<td><a href="#" onclick="fn_showModifyWhitelist(\''+str_mobile+'\',\''+str_bizType+'\')">更改套餐</a></td></tr>';
				
				obj_whitelistBody.html(str_tbodyText);
			} else {
				alert(data.message);
			}
		});
	});
	// 新增初始化dialog
	$('#addWhitelistDialog, #modifyWhitelistDialog').dialog({
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
		
		$('#txt_whitelistMobile').val($('#mobile').val());
		$('#addWhitelistDialog').attr('title', '新增白名单号码').dialog('option', 'title', '新增白名单号码').dialog( "open" );
		
	});
	// 保存白名单事件
	$('#addWhitelistSave').click(function(e) {
		if ( fn_validCookie() ) {
			return;
		}
	
		var str_mobile = $('#txt_whitelistMobile').val(), 
			str_bizType = $('#addWhitelistDialog input[name="biz_type_add"]input:checked').val(), 
			obj_conditionData = {'mobile': str_mobile, 'biz_type': str_bizType};
			
		if ( !fn_validMobile(str_mobile) ) {
			return;
		}
		
		$.post('/whitelist',  JSON.stringify(obj_conditionData), function (data) {
			alert(data.message);
			if ( data.success == 0 ) {
				$('#addWhitelistDialog').dialog('close');
			}
		});
		
	});
	// 套餐修改保存事件
	$('#modifyWhitelistSave').click(function(e) {
		if ( fn_validCookie() ) {
			return;
		}
		
		var str_mobile = $('#txt_modifyWhitelistMobile').html(),
			str_bizType = $('#modifyWhitelistDialog input[name="biz_type_modify"]input:checked').val(), 
			obj_conditionData = {'mobile': str_mobile, 'biz_type': str_bizType};
		
		
		$.ajax({ 
				url: '/whitelist', 
				type: 'PUT',
				dataType: 'json', 
				data: JSON.stringify(obj_conditionData),
				success: function(data){
					alert(data.message);
					if ( data.success == 0 ) {
						$('#modifyWhitelistDialog').dialog('close');
						$('#whitelist_search').click();
					}
				}
		});
		
	});
	fn_unLockScreen();
});

/*
* 验证手机号是否合法
*/
function fn_validMobile(str_mobile, str_msgTitle) {
	var MOBILEREG =  /^(\+86){0,1}1(3[0-9]|5[012356789]|8[02356789]|47)\d{8}$/,
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

// 编辑响应事件
function fn_showModifyWhitelist(str_mobile, str_bizType) {
	if ( fn_validCookie() ) {
		return;
	}
	// 弹出套餐修改页面 并填充数据 
	$('#txt_modifyWhitelistMobile').html(str_mobile);
	$('#modifyWhitelistDialog input[id="biz_type_modify'+ str_bizType +'"]').attr('checked', 'checked');
	$('#modifyWhitelistDialog').attr('title', '套餐修改').dialog('option', 'title', '套餐修改').dialog( "open" );	
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