/*
    *当页面点击查询按钮时，将查询条件保存到cacheDatas中
    *当程序将查询结果返回时，调用cacheDatas中存储的数据，填写到查询输入框中
*/
function fn_PushData(obj,name) {
    if (obj) {
		var element = parent.document.getElementById('cacheDatas'), 
			idArr = obj.split(','), 
			l = idArr.length, str_group = '';
		
		$(element).children().remove();
        if (l > 0) {
            var i = 0, html = '';
            while (i < l) {
                var tmp = idArr[i++];
                if (tmp == 'valid' || tmp == 'category' || tmp == 'status' || tmp == 'service_status' || tmp == 'type' ) { // radio
                   var radios = document.getElementsByName(tmp);
                   var j = 0;
                   while (j < radios.length) {
                        if (radios[j].checked) {
                            html += "<li id='" +tmp+ "'>" +radios[j].value+ "</li>";
                        }
                        j++;
                   }
                   radios = undefined;
                } else if (tmp == 'source_id' || tmp == 'plan_id') { // select
                    html += "<li id='" +tmp+ "'>" +$('#'+tmp).find('option:selected').val()+ "</li>";
                } else if (tmp == 'group') {
					str_group = $('#group').html();
					html += "<li id='" +tmp+ "'>" +$('#'+tmp).val()+ "</li>"; 
				} else {
                    html += "<li id='" +tmp+ "'>" +$('#'+tmp).val()+ "</li>"; 
                }
            }
            $(element).html(html);
            $(element).attr({'name': name, 'groupText': str_group});
            element = undefined;
        }
    }
}
/*
    *当页面重新加载的时候，也就是后台返回查询结果后
    *重新填充上一次的查询条件
    *并清理用于缓存的数据
*/
function fn_PopData(name) {
    var element = parent.document.getElementById('cacheDatas');
	
    if ($(element).attr('name') == name) {
        $(element).children().each(function(index, dom){
            var id = $(dom)[0].id;
            var elementId = '#'+id;
            if (id == 'valid' || id == 'category' || id == 'status' || id == 'service_status' || id == 'type' ) { // radio
                var val = $(dom).text();
                var radios = document.getElementsByName(id);
                if (radios) {
                    var i = 0;
                    while (i < radios.length) {
                        if (radios[i].value == val) {
                            $(radios[i]).attr('checked', true);
							// 业务用户查询如果是家长，套餐类型隐藏
							var $plan = $('.planType');
							if (id == 'category'){
								if(val == '1') {
									$plan.hide();
								} else {
									$plan.show();
								}
							}
                            break;
                        }
                        i++;
                    }
                }
                radios = undefined;
            } else if (id == 'group') {
				var str_group = $(element).attr('groupText'), $group = $('#group');
				$group.html(str_group);
				$('#group option[value='+$(dom).text()+']').attr('selected', true);
			} else if ( id == 'cities' ) {
				$('#cities option[value='+$(dom).text()+']').attr('selected', true);
			} else if ( id == 'corps_hidden' ) {
				var str_hiddenVal = $(dom).text(),
					obj_autoCorpsBakData = $('#corps_input').data('corpdata');
				
				$('#corps_input').val(obj_autoCorpsBakData[str_hiddenVal].ecname);
				$(elementId).val(str_hiddenVal);
			} else { // select and other
                $(elementId).val($(dom).text());
            }
        });
		// 省份的checkbox
		var pro = $(element).attr('province');
		$('input[type=checkbox]').attr('checked', false);
		if (pro) {
			$(pro).attr('checked', true);
		}
    }
    $(element).removeAttr('name');
    element = undefined;
	fn_unLockScreen();
}
