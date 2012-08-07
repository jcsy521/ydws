$(function () {

    //将页面查询到的时间进行转换
	 var timeta= $(".j_timestamp");
	 if (timeta.length != 0) {
		timeta.each(function () {
			 $(this).html(toHumanDate($(this).html()*1000, "no"));
		});		
	 }
	/*
        *修改 iframe中body的样式
    */
    if ($('body').find('#left').length == 0) {
        $('body').css({'padding' : '10px 0px 0px 0px'});
    }
    $('input[type=text],input[type=password]').css({'width':'130px'});
	$('input[type=text]').addClass('text_blur');
	$('input[type=text]').focus(function() {
		$(this).removeClass('text_blur').addClass('text_focus');
	}).blur(function() {
		$(this).removeClass('text_focus').addClass('text_blur');		
	});
    $('select').css({'width':'133px'});
	$('.j_userSelect').css({'width': '260px'});
    $('#showOrHideSearch').toggle(function () {
        $('#searchTable').show();
        $('#showOrHideSearch').text('-');
    },function () {
        $('#searchTable').hide();
        $('#showOrHideSearch').text('+');
    });
	
    $('#provincesNames,#privs').click(function () {
        var pLeft = parent.document.getElementById('left');
        if (pLeft) {
            left = pLeft.clientWidth + 150;
        }
    });
	
    $('legend').click(function () { // fieldset的样式
		$(this).next("form").slideToggle('slow');
	});
	
	//添加控件
	$('#start_time1,#end_time1').datepicker();
	$('#start_time1,#end_time1').datepicker('option', 'maxDate', '0d');
	// 日报时间控件 默认昨天
	$('#daily_time').datepicker();
	$('#daily_time').datepicker('option', 'maxDate', '-1d');
	
	// 业务查询 时间控件
	$('#begintime0, #begintime2').datepicker({
        onSelect: function(dateText, inst) {	// dateText：当前选中日期  inst: 当前日期插件实例
			$('#endtime0, #endtime2').datepicker('option', 'minDate', dateText);	// set minDate is today
	}});
	
	// open business date and close date init
	$('#begintime1').datepicker({
        onSelect: function(dateText, inst) {	// dateText：当前选中日期  inst: 当前日期插件实例
			$('#endtime1').datepicker('option', 'minDate', dateText);	// set minDate is today
	}});
	$('#begintime1').datepicker('option', 'minDate', new Date());	// set minDate is today
	$('#endtime1').datepicker('option', 'minDate', new Date());	// set minDate is today
	
	$('#begintime0, #endtime0, #begintime2, #endtime2, #begintime1, #endtime1').datepicker();
    /*
        *初始化地图页面的大小
        *初始化右侧iframe大小
    */
    var pl = parent.document.getElementById('logo');
    if ($(pl)[0] == undefined) {
        logoHeight = 62;
    } else {
        logoHeight = $(pl)[0].offsetHeight;
	}
	var frameHeight = parent.window.screen.height - logoHeight - 160;
    if ($.browser.msie) {
		frameHeight = parent.window.screen.height - logoHeight - 162;
	} else if (window.google && window.chrome) {
		frameHeight = parent.window.screen.height - logoHeight - 112; 
	}
	$('#frameMap').css({'height': (frameHeight-90)+'px'});
	$('#contantIframe').css({
        'height' : (frameHeight-80)+'px'
    }); 
	$('.juser_type').click(function () {
		$domRadio = $(this), str_radioVal = $domRadio.val(), $plan = $('.planType');
		if (str_radioVal == 1) { // 家长
			$plan.hide();
			//$('#user_typeTh, #user_typeTd').next().remove();
		} else { // 儿童
			$plan.show();
			//$('#user_typeTh').after('<th class="ui-state-default"><div class="DataTables_sort_wrapper">套餐类型<span class="css_right ui-icon ui-icon-carat-2-n-s"></span></div></th>');
			//$('#user_typeTd').after('<td>{{ user["plan"] }}</td>');
		}
	});
	
	//当用户点击导出excel按钮时,进行判断是否有记录
	$('#exportData').click(function () {
		if ($('#rDataTables td').length == 1) {
			alert('没有查询记录，无法导出！');
			return false;
		}
	});
});
//to clear the password for message
function clearSpan() {
	var obj = $(".error");
	if (obj) {
		obj.text("");
	}
}
// 清除文本输入框中的特殊字符
function fn_textKeyUp(obj_this, str_reg) {
	var $tempInput = $(obj_this), str_tempVal = $(obj_this).val();
	if (str_reg == 'text') {
		$tempInput.val(str_tempVal.replace(/[^a-zA-Z0-9\u4e00-\u9fa5\ \_]/g, ''));
	} else if (str_reg == 'user') {
		$tempInput.val(str_tempVal.replace(/[^a-zA-Z0-9\ ]/g, ''));
	} else {
		$tempInput.val(str_tempVal.replace(/[^\d]/g, ''));
	}
} 