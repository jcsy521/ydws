// 页面加载完成后进行加载地图
$(function () {
	$('#start_time1').val(toTodayDate());
	$('#end_time1').val(fn_getNextYearToday());
	
	var obj_prevBtn = $('#prevBtn'),
		obj_nextBtn = $('#nextBtn'), 
		obj_submitBtn = $('#submitBtn'), 
		obj_busGrounp = null;
		
	obj_submitBtn.hide();
	
	// 表单验证, 
	$('#businessFormID1, #businessFormID2, #businessFormID3, #businessFormID4, #businessFormID').validationEngine();
	// 集团名称change时 保存集团手机号
	$('#corps').unbind('change').bind('change', function() {
		//$('#ecmobile').val($('#corps option:selected').attr('ecmobile'));
		
	});
	// 初次加载上页隐藏
	obj_prevBtn.hide();
	
	$('#panelBtn span').click(function(event) {
		var str_id = event.currentTarget.id,
			str_currentId = $('#panelContent div[class*=carCurrent]').attr('id'), 
			n_cNum = fn_getNumber(str_currentId), 
			n_tempNum = 1;
		
		// 根据页面不同所占区域大小不同
		$('#businessPanel').css('height', 300);
		$('#businessPanel #panelContent').css('height', 190);
	
		switch (str_id) {
			case 'prevBtn':
				// 如果在第二页点上一页,隐藏上页操作
				if ( n_cNum == 2 ) {
					obj_prevBtn.hide();
				}
				
				if ( n_cNum > 1 ) {
					n_tempNum = --n_cNum;
				}
				break;
			case 'nextBtn':
				var f_validate = $('#businessFormID'+n_cNum).validationEngine('validate');
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
				$('#ecFormID').submit();
				break;
		}
		
		$('#panelContent .stContent').removeClass('carCurrent');
		
		// 导航标题样式更改为默认
		for ( var i = 1; i < 6; i++ ) {
			$('.ecStep' + i ).css('background-image', 'url("/static/image/busImage/g'+ i +'2.png")');
		}
		
		// 当前内容标题导航更换为当前样式
		$('.ecStep' + n_tempNum ).css('background-image', 'url("/static/image/busImage/g'+ n_tempNum +'1.png")');
			
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
	var n_panelHeight = 300, 
		n_contentHeight = 190;
	
	switch( n_tempNav) {
		case 1: 
			var str_gName = $('#corps').val(), 
				str_gNameId = $('#corps').attr('ecid');
			
			$('#ecid').val(str_gNameId);
			
			$('#tdEcname').html(str_gName);
			break;
		case 2: 
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
			$('#tdColor').html(fn_carColorName(str_cColor));
			$('#tdBrand').html(str_cBrand);
			break;
		case 3:
			var str_Tmobile = $('#terminalMobile').val(), 
				str_Umobile = $('#userMobile').val() || $('#ecmobile').val(), 
				str_nowTime = new Date(),
				str_sfm = str_nowTime.getHours() + ':' + str_nowTime.getMinutes() + ':' + str_nowTime.getSeconds(),
				str_stTime = toTodayDate() + ' ' + str_sfm,
				str_endTime = fn_getNextYearToday() + ' ' + str_sfm,
				n_bicType = parseInt($('#businessFormID3 input[name="corp_corpBiztype"]input:checked').val()),
				str_bizType =  n_bicType ==  0 ? '移动卫士' : '移动外勤';
			
			$('#tmobile').val(str_Tmobile);
			$('#umobile').val(str_Umobile);
			$('#tbegintime').val(toEpochDate(str_stTime));
			$('#tendtime').val(toEpochDate(str_endTime));
			$('#biz_type').val(n_bicType);
			
			$('#tdTmobile').html(str_Tmobile);
			$('#tdUmobile').html(str_Umobile);
			$('#tdBeginTime').html(str_stTime);
			$('#tdEndtime').html(str_endTime);
			$('#tdBizType').html(str_bizType);
			
			n_panelHeight = 400, 
			n_contentHeight = 304;
			break;
	}
	
	// 根据页面不同所占区域大小不同
	$('#businessPanel').css('height', n_panelHeight);
	$('#businessPanel .ecPcontent').css('height', n_contentHeight);
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