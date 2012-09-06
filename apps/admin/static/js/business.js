// 页面加载完成后进行加载地图
$(function () {
	$('#start_time1').val(toTodayDate());
	$('#end_time1').val(fn_getNextYearToday());
	
	var obj_nextBtn = $('#nextBtn'), 
		obj_submitBtn = $('#submitBtn');
		
	obj_submitBtn.hide();
	
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
				if ( n_cNum > 1 ) {
					obj_form.validationEngine('hide');
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
				if ( !f_validate ) {
					return;
				}
				$('#businessFormID'+ (n_cNum-1)).validationEngine('hide');
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
			$('#type').val(str_cType);
			$('#color').val(str_cColor);
			$('#brand').val(str_cBrand);
			
			$('#tdCnum').html(str_cId);
			$('#tdType').html(fn_carTypeName(str_cType));
			$('#tdCcolor').html(str_cColor);
			$('#tdBrand').html(str_cBrand);
			break;
		case 2: 
			var str_Tmobile = $('#terminalMobile').val(), 
				str_stTime = $('#start_time1').val(),
				str_endTime = $('#end_time1').val();
				
			$('#tmobile').val(str_Tmobile);
			$('#begintime').val(toEpochDate(str_stTime+' 00:00:00'));
			$('#endtime').val(toEpochDate(str_endTime+' 00:00:00'));
			
			$('#tdTmobile').html(str_Tmobile);
			$('#tdBeginTime').html(str_stTime);
			$('#tdEndtime').html(str_endTime);
			break;
		case 3: 
			var str_uName = $('#userName').val(), 
				str_uMobile = $('#userMobile').val(),
				str_uAddress = $('#userAddress').val(),
				str_uEmail = $('#userEmail').val();
			
			$('#name').val(str_uName);
			$('#mobile').val(str_uMobile);
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
	var arr_carType = ['','小汽车', '小货车', '大巴车', '摩托车'];
	return arr_carType[parseInt(str_cType)];
}