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
	$('#businessFormID1, #businessFormID2, #businessFormID').validationEngine();
	
	// 初次加载上页隐藏
	obj_prevBtn.hide();
	
	$('#panelBtn span').click(function(event) {
		var str_id = event.currentTarget.id,
			str_currentId = $('#panelContent div[class*=carCurrent]').attr('id'), 
			n_cNum = fn_getNumber(str_currentId), 
			n_tempNum = 1;
		
		// 根据页面不同所占区域大小不同
		$('#businessPanel').css('height', 300);
		$('#businessPanel #panelContent').css('height', 165);
	
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
				if ( n_cNum < 3 ) {
					n_tempNum = ++n_cNum;
				} else {
					n_tempNum = 3;
				}
				// 点击下一页按钮时进行表单的再次验证
				if ( !f_validate ) {
					return;
				}
				// 在第一页点击下一页,显示上一页按钮
				if ( n_cNum == 2 ) {
					obj_prevBtn.show();
				}
				// 表单验证通过隐藏表单提示层
				$('#businessFormID'+ (n_cNum-1)).validationEngine('hide');
				// 取得页面数据进行填充
				fn_fillUserData(n_tempNum - 1);
				break;
			case 'submitBtn':
				n_tempNum = 3;
				fn_fillUserData(n_tempNum);
				$('#ecFormID').submit();
				break;
		}
		
		$('#panelContent .stContent').removeClass('carCurrent');
		
		// 导航标题样式更改为默认
		for ( var i = 1; i < 6; i++ ) {
			$('.cropStep' + i ).css('background-image', 'url("/static/image/busImage/crop'+ i +'2.png")');
		}
		
		// 当前内容标题导航更换为当前样式
		$('.cropStep' + n_tempNum ).css('background-image', 'url("/static/image/busImage/crop'+ n_tempNum +'1.png")');
			
		$('#stepContent' + n_tempNum).addClass('carCurrent');
		
		if ( n_tempNum == 3 ) {
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
			var str_gName = $('#ecName').val();
			
			$('#ecname').val(str_gName);
			
			$('#tdEcname').html(str_gName);
			break;
		case 2: 
			var str_cLink = $('#ecLink').val(), 
				str_cMobile = $('#ecMobile').val(), 
				str_cAddress = $('#userAddress').val(), 
				str_cEmail = $('#userEmail').val();
			
			$('#linkman').val(str_cLink);
			$('#ecmobile').val(str_cMobile);
			$('#address').val(str_cAddress);
			$('#email').val(str_cEmail);
			
			$('#tdEcLink').html(str_cLink);
			$('#tdEcMobile').html(str_cMobile);
			$('#tdEcUserAddress').html(str_cAddress);
			$('#tdEcUserEmail').html(str_cEmail);
			break;
		case 3: 
			n_panelHeight = 600, 
			n_contentHeight = 480;
			
			break;
	}
	
	// 根据页面不同所占区域大小不同
	$('#businessPanel').css('height', n_panelHeight);
	$('#businessPanel .ecPcontent').css('height', n_contentHeight);
} 