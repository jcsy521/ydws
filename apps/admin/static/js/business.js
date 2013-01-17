// 页面加载完成后进行加载地图
$(function () {
	$('#start_time1').val(toTodayDate());
	$('#end_time1').val(fn_getNextYearToday());
	
	var obj_prevBtn = $('#prevBtn'),
		obj_nextBtn = $('#nextBtn'), 
		obj_submitBtn = $('#submitBtn');
		
	obj_submitBtn.hide();
	
	// 初次加载上页隐藏
	obj_prevBtn.hide();
	
	// 表单验证, 
	$('#businessFormID1, #businessFormID2, #businessFormID3, #businessFormID').validationEngine();
		
	$('#panelBtn span').click(function(event) {
		var str_id = event.currentTarget.id,
			str_currentId = $('#panelContent div[class*=carCurrent]').attr('id'), 
			n_cNum = fn_getNumber(str_currentId), 
			n_tempNum = 1, 
			obj_form = $('#businessFormID'+n_cNum);
		
		// 根据页面不同所占区域大小不同
		$('#businessPanel').css('height', 270);
		$('#businessPanel #panelContent').css('height', 165);
		switch (str_id) {
			case 'prevBtn': 
				// 如果在第二页点上一页,隐藏上页操作
				if ( n_cNum == 2 ) {
					obj_prevBtn.hide();
				}
				if ( n_cNum > 1 ) {
					$('.formError').remove();
					n_tempNum = --n_cNum;
				}
				break;
			case 'nextBtn':	
				var f_validate = obj_form.validationEngine('validate');
				if ( n_cNum < 4 ) {
					n_tempNum = ++n_cNum;
				} else {
					n_tempNum = 4;
				}
				// 点击下一页按钮时进行表单的再次验证
				if ( !f_validate ) {
					return;
				} else {
					// 表单验证通过隐藏表单提示层
					$('.formError').remove();
				}
				// 在第一页点击下一页,显示上一页按钮
				if ( n_cNum == 2 ) {
					obj_prevBtn.show();
				}
				// 取得页面数据进行填充
				fn_fillUserData(n_tempNum - 1);
				break;
			case 'submitBtn':
				n_tempNum = 4;
				fn_fillUserData(n_tempNum);
				$('#businessFormID').submit();
				break;
		}
		
		// 当前内容标题导航更换为当前样式
		$('#panelContent .stContent').removeClass('carCurrent');
		
		// 导航标题样式更改为默认
		for ( var i = 1; i < 5; i++ ) {
			$('.step' + i ).css('background-image', 'url("/static/image/busImage/p'+ i +'2.png")');
		}
		
		$('.step' + n_tempNum ).css('background-image', 'url("/static/image/busImage/p'+ n_tempNum +'1.png")');
		
		$('#stepContent' + n_tempNum).addClass('carCurrent');
		
		if ( n_tempNum == 4 ) {
			// 隐藏下页按钮, 显示提交按钮
			obj_nextBtn.hide();
			obj_submitBtn.show();
		} else {
			obj_nextBtn.show();
			obj_submitBtn.hide();
		}
	});
});
// 填充数据 
function fn_fillUserData(n_tempNav) {
	var n_panelHeight = 270, 
		n_contentHeight = 165;
	
	switch( n_tempNav) {
		case 1: 
			var str_cId = $('#carId').val(), 
				str_cType = $('#carType').val(), 
				str_cColor = $('#carColor').val(), 
				str_cBrand = $('#carBrand').val();
			
			$('#cnum').val(str_cId);
			$('#ctype').val(str_cType);
			$('#ccolor').val(str_cColor);
			$('#cbrand').val(str_cBrand);
			
			$('#tdCnum').html(str_cId);
			$('#tdType').html(fn_carTypeName(str_cType));
			$('#tdCcolor').html(fn_carColorName(str_cColor));
			$('#tdBrand').html(str_cBrand);
			break;
		case 2: 
			var str_Tmobile = $('#terminalMobile').val(), 
				str_stTime = $('#begintime1').val(),
				str_endTime = $('#endtime1').val();
				
			$('#tmobile').val(str_Tmobile);
			$('#tbegintime').val(toEpochDate(str_stTime+' 00:00:00'));
			$('#tendtime').val(toEpochDate(str_endTime+' 00:00:00'));
			
			$('#tdTmobile').html(str_Tmobile);
			$('#tdBeginTime').html(str_stTime);
			$('#tdEndtime').html(str_endTime);
			break;
		case 3: 
			var str_uName = $('#userName').val(), 
				str_uMobile = $('#userMobile').val(),
				str_uAddress = $('#userAddress').val(),
				str_uEmail = $('#userEmail').val();
			
			$('#uname').val(str_uName);
			$('#umobile').val(str_uMobile);
			$('#address').val(str_uAddress);
			$('#email').val(str_uEmail);
			
			$('#tdUserName').html(str_uName);
			$('#tdUserMobile').html(str_uMobile);
			$('#tdAddress').html(str_uAddress);
			$('#tdEmail').html(str_uEmail);
			
			n_panelHeight = 430, 
			n_contentHeight = 325;
			break;
		case 4: 
			n_panelHeight = 430, 
			n_contentHeight = 325;
			break;
	}
	
	// 根据页面不同所占区域大小不同
	$('#businessPanel').css('height', n_panelHeight);
	$('#businessPanel #panelContent').css('height', n_contentHeight);
} 
// 通过车辆类型编号获取车辆类型名称 
function fn_carTypeName(str_cType) {
	var arr_carType = ['','小汽车', '小货车', '大巴车', '摩托车', '其他'];
	return arr_carType[parseInt(str_cType)];
}
// 通过车辆颜色编号获取车辆颜色 
function fn_carColorName(str_cColor) {
	var arr_carColor = ['','黑色', '白色', '银色', '红色', '黄色', '灰色', '其他'];
	return arr_carColor[parseInt(str_cColor)];
}