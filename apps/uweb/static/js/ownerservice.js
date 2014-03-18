/**
* 用户服务的手机号及车牌号处理方法 
*/
$(function () {
	$('#userMobile, .j_userCarnum').val('');
	$('.j_userCartype').val('1');
	$('#inputDataPanel, #successPanel').addClass('hidden');
	$('#registerPanel').show();
	
	// 开始登录操作
	$('#userData_register').click(function(e) {
		$('#registerPanel').hide();
		$('#inputDataPanel').show();
		$('#userMobile, .j_userCarnum').val('');
		$('.j_userCartype').val('1');
		$('#userFirstDataPanel').nextAll().remove();
	});
	
	// 新增一车辆
	$('#userCaridAdd').click(function(e) {
		var n_trNums = $('#userInputTable tr').length,
			str_selectHtml = $('#userSelectData').html(),
			str_inputHtml = '<tr><td><select class="j_userCartype">'+ str_selectHtml +'</select></td><td><input type="text" value="" class="input_carnum j_userCarnum" /></td></tr>';
		
		if ( n_trNums >= 11 ) {
			alert('您已添加10个车牌号！');
		}
		$('#userInputTable').append(str_inputHtml);
	});
	
	//同意添加操作
	$('#userDataSaveBtn').click(function(e){
		var str_userMobile = $('#userMobile').val(),
			str_mobileReg = /^\d{11}$/,
			arr_carDatas = [],
			obj_userData = {'umobile': str_userMobile, 'cars': []},
			n_carTypeNum = $('.j_userCartype').length;
		
		// 对用户输入的手机号作简单查验
		if ( str_userMobile == '' ) {
			alert('请输入手机号！');
			return;
		}
		
		if ( !str_mobileReg.test(str_userMobile) ) {
			alert('请输入正确手机号！');
			return;
		}
		
		// 取得用户输入的车牌号及车型信息
		for( var i = 0; i < n_carTypeNum; i++ ) {
			var str_carType = $($('.j_userCartype')[i]).val(), 
				str_carNum = $.trim($($('.j_userCarnum')[i]).val());
			
			if ( str_carNum != '' ) {
				arr_carDatas.push({'car_type': str_carType, 'car_num': str_carNum});
			}
		}
		if ( arr_carDatas.length <= 0 ) {
			alert('请输入车牌号！');
			return;
		}
		obj_userData.cars = arr_carDatas;
		//发送数据
		$.post('/ownerservice', JSON.stringify(obj_userData), function(data) {
			alert(data.message);
			if ( data.status == 0 ) {
				$('#inputDataPanel').hide();
				$('#successPanel').show();
			}
		});
		
	});
	
	// 不同意添加操作
	$('#userDataResetBtn').click(function(e) {
		$('#inputDataPanel, #successPanel').hide();
		$('#registerPanel').show();
	});
});