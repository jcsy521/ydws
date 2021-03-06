﻿//用来判断集团的选择

//用来判断集团的选择
var groupNum = 'yes';
function clickGroup() {
	if (groupNum == 'yes') {
			fn_loadSchool();
			groupNum = 'no';			
		} else {
			return;
		}
}

function fn_changeSchool() {
	var selectCityId = $('#cities').val(); // 选中的option value
	$('#citiesId').val(selectCityId); // 填充到hidden
	fn_loadSchool();
}

function fn_loadSchool () {
	var citiesId = $('#citiesId').val(), // 选中的cityid
		group = $('#corps'),
		cityTemp = [],
		typeTemp = [], // 集团
		type = $('#type').val();
	if ( citiesId != '0' && citiesId != '') { // 如果有选择城市的话 加载集团信息
		cityTemp[0] = parseInt(citiesId, 10);
		var element = parent.document.getElementById('cacheDatas'), // 外层数据
			str_groupVal = '';
		if ( $(element).children().length > 0 ) {
			str_groupVal = $(element).children('li[id=group]').first().html(); // 保存的group的值
		}
		$.get('/corplist', '', function (data) {
			group.empty();
			var groupHtml = '';
			if (data && data.length > 0) {
				groupHtml = '<option value="0">--请选择集团--</option>';
				for (var i = 0; i < data.length; i++) {
					if ( data[i].id == parseInt(str_groupVal) ) { // select 被选中
						groupHtml += '<option value="' +data[i].id+ '" selected="selected">' +data[i].name+ '</option>';
					} else {
						groupHtml += '<option value="' +data[i].id+ '">' +data[i].name+ '</option>';
					}
				}
			} else {
				groupHtml += '<option value="0">-------暂无集团-------</option>';
			}
			group.html(groupHtml);
			pd = null;
		});
	}
}

// group init
function fn_initGroup() {
	groupNum = 'yes';
	$('#group').html('<option value="0">--请选择集团--</option>');
}

/*
* 用户业务变更 
* 个人->集团  or 集团 ->个人
*/ 
function bus_changeUserType(str_ecName, str_tMobile) {
	// 新增初始化dialog
	$('#userTypeChangeDialog').dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		position: [300, 100],
		modal: true,
		resizable: false,
		close: function(e, ui) {
			$('#changeUserType_input').autocomplete('close');
		}
	});
	
	if ( $.browser.msie && parseInt($.browser.version) <= 8 ) {
		$('#userTypeChangeDialog').dialog('option', 'height', '300');
	}
	
	$('#txt_changeTmobile').html(str_tMobile);
	$('#userTypeChangeDialog').attr('title', '业务变更').dialog('option', 'title', '业务变更').dialog( "open" );
	$('#changeUserType_corpName').hide();
	
	if ( str_ecName == '' ) {// 如果是个人切集团
		$('#changeUserType_corpName').show();
		// 提取集团数据
		var obj_corpSelect = $('#corps_select option'),
			arr_autoCorpsData = [],
			n_corpSelectOptions = $('#corps_select option').length,
			obj_corpsSearch = $('#changeUserType_input');
			
		if ( n_corpSelectOptions > 0 ) {
			//获取集团数据
			obj_corpSelect.each(function(e) {
				var str_corpName = $(this).html(),
					str_ecId = $(this).attr('value');
				
				if ( str_corpName != '全部' ) {
					arr_autoCorpsData.push({'label': str_corpName, 'value': str_ecId});
				}
			});
			// 集团下拉框图标事件	
			$('#changeUserType_sign').unbind('click').click(function(e) {
				var b_autoCompleteSt = $('.ui-autocomplete').is(':visible');
				
				if ( b_autoCompleteSt ) {
					obj_corpsSearch.autocomplete('close');
				} else {
					obj_corpsSearch.autocomplete('search', '');
				}
			});
			fn_initAutoUserTypeChange(arr_autoCorpsData);
			
			var str_fstVal = arr_autoCorpsData[0].label
				str_fstEcid = arr_autoCorpsData[0].value;
			
			obj_corpsSearch.val(str_fstVal);
			$('#changeUserType_hidden').val(str_fstEcid);
		}
	}
	// 变更保存
	$('#changUserTypeSave').unbind('click').click(function(e) {
		var obj_postData = {};
		
		if ( str_ecName == '' ) {
			obj_postData = {'cid': $('#changeUserType_hidden').val(), 'tmobile': str_tMobile};
		} else {
			obj_postData = {'tmobile': str_tMobile};
		}
		
		$.post('/usertype',  JSON.stringify(obj_postData), function (data) {
			if ( data.status == 0 ) {
				alert('操作成功，请重新查询！');
				$('#userTypeChangeDialog').dialog('close');
			} else {
				alert(data.message);
			}
		});
	});
}

/**
* 初始化短信接收号码的autocomplete
*/
function fn_initAutoUserTypeChange(arr_autoCorpsData) {
	var obj_compelete = $('#changeUserType_input');
	
	// autocomplete	自动完成 初始化
	obj_compelete.autocomplete({
		minLength: 0,
		source: arr_autoCorpsData,
		select: function(event, ui) {			
			var obj_item = ui.item,
				str_tLabel = obj_item.label,
				str_tVal = obj_item.value;
			
			$('#changeUserType_hidden').val(str_tVal);
			obj_compelete.val(str_tLabel);
			return false;
		}
	});
}

// 更改个人或者集团 的登录账号
function fn_changeUserName(str_userType, str_oUser) {
	$('#txt_oldUsername').html(str_oUser); 
	$('#txt_newChangeUsername').val('').removeClass('text_blur').css({'width':'220px'}).unbind('focus blur');
	
	// 初始化dialog
	$('#changeUserNameDialog').dialog({
		autoOpen: true,
		height: 200,
		width: 350,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	
	//保存
	$('#changeUsernameSave').unbind('click').click(function(e) {
		var str_newUsername = $.trim($('#txt_newChangeUsername').val()),
			obj_conditionData = {'old_username': str_oUser, 'new_username': str_newUsername,'user_type': str_userType};
		
		/*
		* 验证手机号是否合法
		*/
		var MOBILEREG = /^[0-9]{11}$/;/*/^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/;*/
		
		if ( str_newUsername == '' ) {
			alert('请输入用户手机号！');
			return;
		}
		
        
		if ( !MOBILEREG.test(str_newUsername) ) {	// 手机号合法性验证
			alert('您输入的用户手机号不合法，请重新输入！');
			return;
		}
        
		$.post('/username',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.status == 0 ) {
				alert('账号已修改，请查看。');
				$('#changeUserNameDialog').dialog('close');
			} else {
				alert(data.message);
			}
		});
		
	});
	
}


//删除终端的限制功能
function fn_delTerminalLimit(mobile, ip) {
	// 初始化dialog
	$('#delLimitDialog').dialog({
		autoOpen: true,
		height: 200,
		width: 350,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	
	$('#delLimitMobile').html(mobile);
	
	$('#delLimitIp').html(ip);
	
	//保存
	$('#delLimit_submit').unbind('click').click(function(e) {
		var str_delck1 = $('#clearDataCk1').attr('checked'),
			str_delck2 = $('#clearDataCk2').attr('checked'),
			str_mobile = $('#delLimitMobile').html(),
			str_ip = $('#delLimitIp').html(),
			str_url = '/register/delete?umobile=';
		
		if ( str_delck1 ) {
			str_url += ''+str_mobile;
		}
		if ( str_delck2 ) {
			str_url += '&remote_ip='+str_ip;
		}
		str_url += '&flag=del';
		
		fn_lockScreen('删除操作进行中...');
		$.get(str_url, function (data) {
			fn_unLockScreen();
			if ( data.status == 0 ) {
				$('#delLimitDialog').dialog('close');
			} else {
				alert("删除失败。");
			}
		});
	});
	
	//取消
	$('#delLimit_cancel').unbind('click').click(function(e) {
		$('#delLimitDialog').dialog('close');
	});
}

//终端参数编辑功能
function fn_editTerminalSetting(mobile, str_setKey, str_setVal) {
	// 初始化dialog
	$('#editTerminalSettingDialog').dialog({
		autoOpen: true,
		height: 200,
		width: 350,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	
	$('#terminalset_mobile').html(mobile);	
	$('#terminalset_setKey').html(str_setKey);
	$('#terminalset_setVal').val('');
	
	//保存
	$('#editerminal_submit').unbind('click').click(function(e) {
		var str_mobile = $('#terminalset_mobile').html(),
			str_setKey = $('#terminalset_setKey').html(),
			str_setVal = $('#terminalset_setVal').val(),
			obj_setPost = {'tmobile': str_mobile, 'key': str_setKey, 'value': str_setVal};
			
		
		fn_lockScreen('操作进行中...');
		$.ajax({ 
				url: '/setting', 
				type: 'PUT',
				dataType: 'json', 
				data: JSON.stringify(obj_setPost),
				success: function(data){
					fn_unLockScreen();
					if ( data.status == 0 ) {
						alert("修改成功。");
						$('#editTerminalSettingDialog').dialog('close');
					} else {
						alert("操作失败。");
					}
				}
		});
	});
	
	//取消
	$('#editerminal_cancel').unbind('click').click(function(e) {
		$('#editTerminalSettingDialog').dialog('close');
	});
}
