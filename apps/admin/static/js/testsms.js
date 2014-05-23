/**
* Test短信相关操作
*/

// 基本方法
$(function () {
	// 设置标题头样式
	$('#search_table th').addClass('ui-state-default');
	
	// 查询号码是否在白名单中事件侦听 
	$('#test_search').click(function(e) {
		fn_validCookie();
		
		var str_mobile = $('#mobile').val(), 
			obj_conditionData = {'mobile': str_mobile},
			obj_testsmsBody = $('#testsms_tbody');
		//clear old data
		obj_testsmsBody.html('');
		
		// 检查号码格式
		if ( !fn_validMobile(str_mobile) ) {
			return;
		}
		
		$.post('/testsms',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.status == 0 ) {
				var str_tbodyText ='<tr>',
					obj_tempData = data.res,
					str_mobile = obj_tempData.mobile,
					str_switch = obj_tempData.test,
					str_switch_name = '开启';
				
				if ( str_switch == 0 ) {
					str_switch_name = '关闭';
				}
				str_tbodyText += '<td class="sorting_1">'+str_mobile+'</td>';
				str_tbodyText += '<td class="sorting_1">'+str_switch_name+'</td>';
				str_tbodyText += '<td class="sorting_1"><a href="#" onclick="fn_modifyTest(\''+str_mobile+'\',\''+str_switch+'\')">更改</a></td></tr>';
				
				obj_testsmsBody.html(str_tbodyText);
			} else {
				alert(data.message);
			}
		});
	});
	// clear overlayer
	fn_unLockScreen();
});

/*
* 验证手机号是否合法 TODO: why?
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

// 编辑响应事件
function fn_modifyTest(str_mobile, str_test) {
    // 检测cookie 是否有效
	if ( fn_validCookie() ) {
		return;
	}
	// 弹出套餐修改页面 并填充数据 
	var str_test = str_test == '0' ? 1 : 0;
	var obj_conditionData = {'mobile':str_mobile,
	                         'test':str_test}
	$.ajax({ 
		url: '/testsms', 
		type: 'PUT',
		dataType: 'json', 
		data: JSON.stringify(obj_conditionData),
		success: function(data){
			alert(data.message);
			if ( data.status == 0 ) {
				$("#test_search").click();
			}
		}
	});
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