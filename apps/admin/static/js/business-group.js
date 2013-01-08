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
			$('.ecStep' + i ).css('background-image', 'url("/static/image/busImage/g'+ i +'2.png")');
		}
		
		// 当前内容标题导航更换为当前样式
		$('.ecStep' + n_tempNum ).css('background-image', 'url("/static/image/busImage/g'+ n_tempNum +'1.png")');
			
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
					response( $.map(cache[ term ], function(item) {
							var str_ecName = item.ec_name, 
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