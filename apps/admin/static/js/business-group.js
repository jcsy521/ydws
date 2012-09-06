// 页面加载完成后进行加载地图
$(function () {
	$('#start_time1').val(toTodayDate());
	$('#end_time1').val(fn_getNextYearToday());
	
	var obj_nextBtn = $('#nextBtn'), 
		obj_submitBtn = $('#submitBtn'), 
		obj_busGrounp = null;
		
	obj_submitBtn.hide();
	
	// 表单验证, 
	$('#businessFormID1, #businessFormID2, #businessFormID3, #businessFormID4, #businessFormID').validationEngine();
	
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
				if ( n_cNum > 1 ) {
					n_tempNum = --n_cNum;
				}
				break;
			case 'nextBtn':
				var f_validate = $('#businessFormID'+n_cNum).validationEngine('validate');
				if ( n_cNum < 5 ) {
					n_tempNum = ++n_cNum;
				} else {
					n_tempNum = 5;
				}
				if ( !f_validate ) {
					return;
				}
				$('#businessFormID'+ (n_cNum-1)).validationEngine('hide');
				// 取得页面数据进行填充
				fn_fillUserData(n_tempNum - 1);
				break;
			case 'submitBtn':
				n_tempNum = 5;
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
		
		if ( n_tempNum == 5 ) {
			// 隐藏下页按钮, 显示提交按钮
			obj_nextBtn.hide();
			obj_submitBtn.show();
		} else {
			obj_nextBtn.show();
			obj_submitBtn.hide();
		}
	});
	// 动态加载集团信息
	var cache = [];
	
	$('#ecName').keyup(function(event) {
			if ( event.keyCode === $.ui.keyCode.TAB && $(this).data('autocomplete').menu.active ) {
				event.preventDefault();
			}
			var str_text = '<input type="text" class="validate[required,custom[mobile]] text_blur" maxlength="11" id="ecMobile" style="width: 120px;"><span class="redColor">*</span>';
			
			$('#ecMobilePanel').html(str_text);
			
			$('#ecName').autocomplete('search');
		}).blur(function(event) {
			var str_nameVal = $('#ecName').val();
			if ( obj_busGrounp ) { 
				for ( var i = 0; i < obj_busGrounp.length; i++ ) {
					var obj_tempData = obj_busGrounp[i], 
						str_dataName = obj_tempData.ec_name;
					
					if ( str_dataName == str_nameVal ) {
						var str_text = '<label class="text_label" id="ecMobile" value="'+ obj_tempData.mobile +'">'+ obj_tempData.mobile +'</label><span class="redColor">*</span>'
						$('#ecMobilePanel').html(str_text);
					}
				}
			}
		}).autocomplete({
			source: function(request, response) { 
				var term = request.term;

				if ( term in cache ) {
				// todo处理中...
					response( $.map(cache[ term ], function(item) {
							var str_ecName = item.ec_name, 
								str_ecMobile = item.mobile, 
								str_inputText = $('#ecName').val();
							
							if ( str_ecName.search(str_inputText) != -1 ) {
								return {
									label: item.ec_name,
									value: item.ec_name, 
									value2: item.mobile
								}
							}
						}));
					return;
				}

				$.ajax({
					url: '/ecbusiness/asyncfill',
					dataType: 'json',
					async: true, 
					success: function(data) { 
						cache[term] = data;
						obj_busGrounp = data;
						
						response( $.map(data, function(item) {
							var str_ecName = item.ec_name, 
								str_ecMobile = item.mobile, 
								str_inputText = $('#ecName').val();
							
							if ( str_ecName.search(str_inputText) != -1 ) {
								return {
									label: item.ec_name,
									value: item.ec_name, 
									value2: item.mobile
								}
							}
						}));
					}
				});
			},
			select: function(event, ui) { 
				var str_text = '<label class="text_label" id="ecMobile" value="'+ ui.item.value2 +'">'+ ui.item.value2 +'</label><span class="redColor">*</span>'
				$('#ecMobilePanel').html(str_text);
			},
			open: function() { 
				$( this ).removeClass('ui-corner-all').addClass('ui-corner-top');
			},
			close: function() { 
				$( this ).removeClass('ui-corner-top').addClass('ui-corner-all');
			}
		});
});
// 填充数据 
function fn_fillUserData(n_tempNav) {
	var n_panelHeight = 300, 
		n_contentHeight = 190;
	
	switch( n_tempNav) {
		case 1: 
			var str_gName = $('#ecName').val(), 
				str_gMobile = $('#ecMobile').attr('value');
			
			$('#ecname').val(str_gName);
			$('#ecmobile').val(str_gMobile);
			
			$('#tdEcname').html(str_gName);
			$('#tdEcmobile').html(str_gMobile);
			break;
		case 2: 
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
			$('#tdColor').html(str_cColor);
			$('#tdBrand').html(str_cBrand);
			break;
		case 3:
			var str_Tmobile = $('#terminalMobile').val(), 
				str_stTime = $('#start_time1').val(),
				str_endTime = $('#end_time1').val();
				
			$('#tmobile').val(str_Tmobile);
			$('#begintime1').val(toEpochDate(str_stTime+' 00:00:00'));
			$('#endtime1').val(toEpochDate(str_endTime+' 00:00:00'));
			
			$('#tdTmobile').html(str_Tmobile);
			$('#tdBeginTime').html(str_stTime);
			$('#tdEndtime').html(str_endTime);
			break;
		case 4:
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
			
			n_panelHeight = 600, 
			n_contentHeight = 480;
			break;
		case 5: 
			n_panelHeight = 600, 
			n_contentHeight = 480;
			
			break;
	}
	
	// 根据页面不同所占区域大小不同
	$('#businessPanel').css('height', n_panelHeight);
	$('#businessPanel .ecPcontent').css('height', n_contentHeight);
} 
// 通过车辆类型编号获取车辆类型名称 
function fn_carTypeName(str_cType) {
	var arr_carType = ['','小汽车', '小货车', '大巴车', '摩托车'];
	return arr_carType[parseInt(str_cType)];
}