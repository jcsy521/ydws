//用来判断集团的选择

//用来判断集团的选择
var groupNum = 'yes';
function clickGroup() {
	if (groupNum == 'yes') {
			fn_loadSchool();
			groupNum = 'no';			
		} else {
			return;
		}
}
function fn_changeSchool() {
	var selectCityId = $('#cities').val(); // 选中的option value
	$('#citiesId').val(selectCityId); // 填充到hidden
	fn_loadSchool();
}
function fn_loadSchool () {
	var citiesId = $('#citiesId').val(), // 选中的cityid
		group = $('#corps'),
		cityTemp = [],
		typeTemp = [], // 集团
		type = $('#type').val();
	if ( citiesId != '0' && citiesId != '') { // 如果有选择城市的话 加载集团信息
		cityTemp[0] = parseInt(citiesId, 10);
		var element = parent.document.getElementById('cacheDatas'), // 外层数据
			str_groupVal = '';
		if ( $(element).children().length > 0 ) {
			str_groupVal = $(element).children('li[id=group]').first().html(); // 保存的group的值
		}
		$.get('/corplist', '', function (data) {
			group.empty();
			var groupHtml = '';
			if (data && data.length > 0) {
				groupHtml = '<option value="0">--请选择集团--</option>';
				for (var i = 0; i < data.length; i++) {
					if ( data[i].id == parseInt(str_groupVal) ) { // select 被选中
						groupHtml += '<option value="' +data[i].id+ '" selected="selected">' +data[i].name+ '</option>';
					} else {
						groupHtml += '<option value="' +data[i].id+ '">' +data[i].name+ '</option>';
					}
				}
			} else {
				groupHtml += '<option value="0">-------暂无集团-------</option>';
			}
			group.html(groupHtml);
			pd = null;
		});
	}
}
// group init
function fn_initGroup() {
	groupNum = 'yes';
	$('#group').html('<option value="0">--请选择集团--</option>');
}
