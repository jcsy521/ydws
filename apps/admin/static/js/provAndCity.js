// 返回传递字符串中的数字
function fn_returnNum(strings) {
	return strings.replace(/\D/g,'');
}

/*
    *插件dialog and dialog's html
*/
var dialog_status = "closing";
/*
    *who:dialog's id
    *whoName:title name
    *btns:bouttos
    *left:dialog position'left
*/
function makeDialog(who, whoName, btns, left){
    $(who).dialog({
        "autoOpen": true,
        "title": whoName,
        "buttons": btns,
		"modal": true,
		"position": [left],
        "minHeight": 300,
        "width": 540,
        "resizable": true,
        "open": function (event, ui) {
            $('.ui-widget-overlay').css({'opacity':'0.2'});
        }
    });
	//dialog的X事件
	$('.ui-icon-closethick').click(function () {
        fn_ClearDialogData();
	});
}

function fn_ClearDialogData() { 
	$('.ui-icon-closethick').unbind('click'); // 解绑定dialog关闭按钮的点击事件
}
//按钮
var btn = {
		"确定": function () {
			commitClick();
			$('.ui-icon-closethick').unbind('click'); // 解绑定dialog关闭按钮的点击事件
			$(this).dialog("close");
		},
		"取消": function () {
			$('.ui-icon-closethick').unbind('click'); // 解绑定dialog关闭按钮的点击事件
			$(this).dialog("close");
		}
	}
// 初始化数据 打开dialog
function _ajaxGetData(who) {
	makeDialog("#d_cities", "城市", btn, 350);
	fn_selectCurrentCities();
	$('.ckList').css({'display':'inline'});
}
// 选中城市后 确定事件
function commitClick() {
	var	str_cityIds = '',
		str_cityNames = '';
	$('.j_cities input[type=checkbox]').each(function() {
		if ($(this).attr('checked')) {
			var id = $(this).attr('id').substr(8),
				str_name = $('#span'+id).html();
			str_cityNames += str_name + '+';
			str_cityIds += id + ',';
		}
	});	
	str_cityNames = str_cityNames.substr(0, str_cityNames.length-1);
	str_cityIds = str_cityIds.substr(0, str_cityIds.length-1);
	$('#citiesNames').val(str_cityNames);
	if ($('#checkAll:not(:hidden)').attr('checked') == true) {
		$('#cities').val('0');
	} else {
		$('#cities').val(str_cityIds);
	}
}

// 默认市被选中
function fn_selectCurrentCities() {
	var $cities = $('.j_CurrentCities'), // 默认city
		$checkCity = $('.j_ckCity'), // 所有的城市
		n_cities = 0,
		n_checkCity = 0, // 所有checkbox
		str_names = '',
		str_ids = '',
		$currentCities = $('#cities'),
		$citiesNames = $('#citiesNames'),
		$normalUserCity = $('#normalUserCity'); 
	if ( $cities && $checkCity ) { //超级管理员
		n_cities = $cities.length; 
		n_checkCity = $checkCity.length;
		if ( n_cities == n_checkCity ) { // 全选选中 所有checkbox都选中
			$('#checkAll').attr('checked',  true);
		}
		// 用户城市 被选中
		for ( var i = 0; i < n_checkCity; i++ ) {
			for ( var j=0; j < n_cities; j++ ) {
				if ( $checkCity[i].value == $cities[j].value ) {
					$checkCity[i].checked = "true";
					str_ids = str_ids + $cities[j].value+",";
					str_names = str_names + $cities[j].name+"+";
				}
			}
		}
		str_ids = str_ids.substr(0,str_ids.length-1);
		str_names = str_names.substr(0,str_names.length-1);
		if ($('#checkAll:not(:hidden)').attr('checked') == true) {
			$currentCities.val('0'); // 全选
		} else {
			$currentCities.val(str_ids);
		}
		$citiesNames.val(str_names);
	} 
	//普通管理员
	if ( $normalUserCity.length>0 ) {
		$cities.each(function() {
			str_ids = str_ids + $(this).val()+",";
			str_names = str_names + $(this).attr('name')+"+";
		});
	str_ids = str_ids.substr(0,str_ids.length-1);
	str_names = str_names.substr(0,str_names.length-1);
	$normalUserCity.html(str_names);
	$currentCities.val(str_ids);
	}
}
// 全选
function f_AllChooses() {
        if ($('#checkAll:not(:hidden)').attr('checked') == true) {
			//allProvs += currentCityId + ',';
            $('#checkAll:not(:hidden)').parent().children('ul:not(:hidden)')
            .find('input').attr('checked', true);
        } else {
            $('#checkAll:not(:hidden)').parent().children('ul:not(:hidden)')
            .find('input').removeAttr('checked', true);
        }
}
// 全选失效
function disabledAllChoose() {
	var n_checkedLenth = $('.j_cities input[checked=true]').length, //选中的checkbox个数
		n_allLength = $('.j_cities input[type=checkbox]').length;	// 总共checkbox个数
	if ( n_checkedLenth == n_allLength ) {
		$('#checkAll:not(:hidden)').attr('checked', true);
	} else {
		//城市的全选按钮失效
		$('#checkAll:not(:hidden)').attr('checked', false);
	}
}
/*change city */
function fn_changeCity() {
	var selectCityId = $(this).val(); // 选中的option value
	$('#citiesId').val(selectCityId); // 填充到hidden
}