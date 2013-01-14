/**
* 集团用户操作方法
* obj_carsData: 存储lastinfo中所有终端的信息
* str_currentTid: 上次lastinfo的选中终端tid
* arr_autoCompleteData: autocomplete 查询数据
*/
var obj_carsData = {},
	str_currentTid = '',
	arr_autoCompleteData = [],
	str_checkedNodeId = '',
	arr_staticsData = [],	// 后台查询到的报警记录数据
	pagecnt = -1,	// 查询到数据的总页数,默认-1
	n_pageNum = 0,	// 当前所在页数
	obj_oldData = {'gids': '', 'tids': '', 'n_gLen': 0};
	
(function() {

/**
*  创建右键菜单，设置每个节点的菜单右键菜单
*/
function customMenu(node) {
	var obj_node = $(node),
		items = null,		// 菜单的操作方法
		renameLabel = '',	// 重命名lable
		createLable = '',	// 新建lable
		deleteLable = '';	// 删除lable
	
	if ( obj_node.hasClass('j_corp') ) {		// 集团右键菜单
		renameLabel = '重命名集团';
		createLable = '新建分组';
		deleteLable = '删除集团';
	} else if (obj_node.hasClass('j_group')) {	// 组右键菜单
		renameLabel = '重命名组名';
		deleteLable = '删除分组';
		createLable = '新建终端';
	} else {									// 终端右键菜单
		renameLabel = '编辑终端';
		deleteLable = '删除终端';
	}
	
	items = {
		"create" : {
			"label" : createLable,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				if ( obj_this.hasClass('j_group') ) {
					fn_initCreateTerminal('', obj_this.children('a').eq(0).attr('groupId'));
					return false;
				}
				this.create();
			}
		},
		"rename" : {
			"label" : renameLabel,   //Different label (defined above) will be shown depending on node type
			"action" : function(obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_leafNode') ) {	// 编辑终端
					fn_initEditTerminal(obj_this.children('a').eq(0).attr('tid'));
					return false;
				}
				this.rename(obj);
			}
		},
		"remove" : {
			"label" : deleteLable,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_corp') ) {	//  删除集团
					alert('集团不能删除。');
					return;
				} else if ( obj_this.hasClass('j_group') ) {	// 删除组
					// todo 判断是否有终端 
					var n_terminalLength = obj_this.children('ul').length,
						str_gid = obj_this.children('a').attr('groupid');
						
					if ( n_terminalLength > 0 ) {
						alert('该分组下有终端不能删除.');
						return;
					} else {
						if ( confirm('确定要删除该组吗？') ) {
							this.remove(obj);
						}						
					}
				} else {	// 删除终端
					if ( confirm('确定要删除该终端吗？') ) {
						this.remove(obj);
					} else {
						return;
					}
				}
			}
		}
	};
   //If node is a folder do not show the "delete" menu item
   if ( obj_node.hasClass('j_leafNode') ) {
	  delete items.create;
   }
   if ( obj_node.hasClass('j_corp')  ) {
		delete items.remove;
   }
   if ( obj_node.hasClass('j_group') && obj_node.children('a').attr('title') == '未分组' ) {
		delete items.remove;
		delete items.rename;
   }
   return items;
}
	
/*
* dnd: drag
* contextmenu: right-menu
* types: node icon
* crrm: create、remove、rename等
*/
window.dlf.fn_loadJsTree = function(str_checkedNodeId,str_html) {
	$('#corpTree').jstree({
		"plugins": [ "themes", "html_data", "ui", "contextmenu",'crrm', "types", 'dnd' ],
		'html_data': {
			'data': str_html
		},
		"contextmenu" : {
			'items': customMenu,
			'select_node': true
		},
		'ui': {
			'initially_select': str_checkedNodeId
		},
		"crrm" : {
			"move": {
				"check_move" : function (m) {
					var obj_currentNode = m.o,
						p = this._get_parent(obj_currentNode);	// get  parent of the node
					
					if ( !p ) {
						return false;
					}
					p = p == -1 ? this.get_container() : p;
					
					if( p === m.np ) return true;	// 如果移动到自己的父节点下
					if( p[0] && m.np[0] && p[0] === m.np[0] ) {
						return true;
					}
					// 如果 要移动节点的父节点  和  目标节点  是同一级 则可以移动
					var obj_currentPrentNode = $(p[0]),
						obj_currentA = obj_currentNode.children('a').eq(0),
						str_tid = obj_currentA.attr('tid'),
						str_parent = obj_currentPrentNode.hasClass('j_group'),
						obj_targetNode = $(m.np[0]),
						str_targetGroupId = obj_targetNode.children('a').eq(0).attr('groupId'),
						str_target = $(m.np[0]).hasClass('j_group'),
						arr_tids = [];
					
					if ( str_parent && str_target ) {
						arr_tids.push(str_tid);
						fn_moveGroup(arr_tids, str_targetGroupId);
						return true;
					}
					return false;
				}
			}
		}
	}).bind('rename.jstree', function(e, data) {	// 重命名
		var	obj_rslt = data.rslt,
			obj_currentNode = $(obj_rslt.obj[0]),
			obj_current = obj_currentNode.children('a').eq(0),
			str_newName = obj_rslt.new_name,
			b_flag = obj_currentNode.hasClass('j_leafNode');
			
		if ( str_newName == data.rslt.old_name && !b_flag ){	// 如果新名称和旧名称相同 不操作
			return;
		}
		if ( obj_currentNode.hasClass('j_group') ) {	// 重命名组	
			fn_renameGroup(obj_current.attr('groupid'), str_newName, data.rlbk);
		} else if ( obj_currentNode.hasClass('j_corp') ) {	// 重命名集团
			fn_renameCorp(obj_current.attr('corpid'), str_newName, data.rlbk)
		} else if ( b_flag ) {	// 编辑终端
			//fn_initEditTerminal(obj_current.attr('tid'));
		}
	}).bind('remove.jstree', function(e, data) {	// 删除节点
		var obj_rslt = data.rslt,
			obj_currentNode = $(obj_rslt.obj[0]),
			obj_current = obj_currentNode.children('a').eq(0);
			
		if ( obj_currentNode.hasClass('j_group') ) {	// 删除组
			fn_removeGroup(obj_current.attr('groupid'), data.rlbk);
		} else if ( obj_currentNode.hasClass('j_leafNode') ) {	// 删除终端
			fn_removeTerminal(obj_current.attr('tid'), data.rlbk);
		}
	}).bind('create.jstree', function(e, data) {	// 新建节点
		var obj_rslt = data.rslt,
			obj_newNode = $(obj_rslt.obj[0]),
			obj_parent = $(obj_rslt.parent[0]);
			
		if ( obj_parent.hasClass('j_group') ) {	// 新建终端
			//obj_newNode.addClass('j_terminal terminalNode');
			//fn_initCreateTerminal(obj_newNode.children('a'), obj_parent.children('a').attr('groupId'));
		} else if ( obj_parent.hasClass('j_corp') ) {	// 新建分组
			obj_newNode.addClass('j_group');
			fn_createGroup($('.corpNode').attr('corpid'), obj_rslt.name, obj_newNode.children('a'));
		}
	}).bind('loaded.jstree', function(e, data) {	// 树节点加载完成事件
		// 循环所有终端 找到当前终端并更新车辆信息
		var b_loop = true;
		if ( obj_carsData ) {
			for ( var param in obj_carsData ) {
				var obj_car = obj_carsData[param],
					n_clon = obj_car.clongitude/NUMLNGLAT,	
					n_clat = obj_car.clatitude/NUMLNGLAT;
					
				if ( n_clon != 0 && n_clat != 0 ) {
					dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
				}
			}
			if ( str_currentTid != undefined && str_currentTid != '') {
				for(var param in obj_carsData) {
					var obj_carInfo = obj_carsData[param], 
						str_tid = param;
					
					if ( str_currentTid == str_tid ) {	// 更新当前车辆信息
						dlf.fn_updateTerminalInfo(obj_carInfo);
						b_loop = false;
					}
				}
			} else {	// 第一次发起switchCar启动lastinfo
				var obj_current = $('#' + data.inst.data.ui.to_select);

				str_currentTid = obj_current.attr('tid');
				dlf.fn_switchCar(str_currentTid, obj_current);
			}
			/*if ( b_loop ) {
				data.inst.open_all(0); // -1 opens all nodes in the container
				dlf.fn_updateTerminalInfo(obj_carsData[$('.j_terminal').eq(0).attr('tid')]);
			}*/
		}
	}).bind('click.jstree', function(event, data) {	// 选中节点事件
		var str_target = event.target.nodeName, 
			obj_current = $(event.target),
			b_terminalClass = obj_current.hasClass('j_terminal');
			
		if ( b_terminalClass && ( str_target == 'A' || str_target == 'INS') ) {                   
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				return;
			}
			str_currentTid =  str_tid;	// todo
			str_checkedNodeId = 'leaf_' + str_tid;	
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,            
		} else {
			return false;
		}
	});
}

/**
* 集团用户 lastinfo
*/
window.dlf.fn_corpGetCarData = function() {
	var obj_current = $('.j_leafNode a[class*=jstree-clicked]'),
		str_checkedNodeId = obj_current.attr('id');	// 上一次选中车辆的id
		
	str_currentTid = obj_current.attr('tid');	// load.jstree时更新选中的车
	$.post_(CORP_LASTINFO_URL, '', function (data) {	// 向后台发起lastinfo请求
			if ( data.status == 0 ) {
				var obj_corp = data.res,
					arr_groups = obj_corp.groups,	// all groups 
					n_groupLength = arr_groups.length,	// group length
					n_onlineCnt = obj_corp.online,		// online count
					n_offlineCnt = obj_corp.offline,	// offline count
					str_corpName = obj_corp.name,	// corp name
					str_corpId = obj_corp.cid,		// corp id
					str_html = '<ul>',
					str_groupIds = ',', // 组ID组
					arr_tids = [], 	// 组下的tid组
					str_tempFirstTid = '',	// 默认第一个tid
					str_groupFirstId = '',	// 默认第一个groupid
					obj_newData = {};
				
				if ( str_corpId && str_corpName ) {
					str_html += '<li class="j_corp"><a title="'+ str_corpName +'" corpid="'+ str_corpId +'" class="corpNode" href="#">'+ str_corpName +'</a>';
				}
				
				arr_autoCompleteData = [];
				$('.carCount').html( n_onlineCnt + n_offlineCnt );
				$('.onlineCount').html(n_onlineCnt);
				$('.offlineCount').html(n_offlineCnt);
				if ( n_groupLength > 0 ) {
					str_html += '<ul>';
					str_groupFirstId = 'group_' + arr_groups[0].id
					for ( var i = 0; i < n_groupLength; i++ ) {	// 添加组
						var obj_group = arr_groups[i],
							str_groupName = obj_group.name,
							str_groupId = obj_group.gid,
							arr_cars = obj_group.cars,
							str_tids = ',', //tid组
							n_carsLength = arr_cars.length;
							//arr_tids = [];
							
						str_html += '<li class="j_group"><a href="#" class="groupNode" groupId="'+ str_groupId +'" title="'+ str_groupName +'" id="group_'+ str_groupId +'">'+ str_groupName +'</a>';
						
						if ( n_carsLength > 0 ) {
							str_html += '<ul>';
							str_tempFirstTid = 'leaf_' + arr_cars[0].tid;
							for ( var x = 0; x < n_carsLength; x++) {	// 添加组下面的终端
								var obj_car = arr_cars[x],
									str_tid = obj_car.tid,
									str_alias= obj_car.alias,
									str_login = obj_car.login;
									
								obj_carsData[str_tid] =  obj_car;
								//arr_tids.push(str_tid);	// 填充tid
								str_tids += str_tid + ','; //tid组string 串
								if ( str_login == LOGINOUT ) {
									str_html += '<li class="jstree-leaf j_leafNode"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_alias +'" class="terminalNode j_terminal" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';
								} else {
									str_html += '<li class="jstree-leaf j_leafNode"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_alias +'" class="terminalNode j_terminal" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';
								}
								/** 
								* 自动完成数据填充:根据旅客姓名和手机号进行搜索
								*/
								arr_autoCompleteData.push({label: str_alias, value: str_tid});
								
							}
							str_html += '</li></ul>';
							// 填充本次数据 为了与下次lastinfo进行比较
							
							arr_tids[str_groupId] = str_tids;
						}
						str_groupIds += str_groupId + ',';
					}
					// 存储 gids , tids
					obj_newData = {'gids': str_groupIds, 'tids': arr_tids, 'n_gLen': n_groupLength};
				}
				$('.j_carList').data('carsData', obj_carsData);	// 存储所有终端信息
				str_html += '</li></ul>';
				var str_tempNodeId = '';
				if ( str_checkedNodeId == '' || str_checkedNodeId == undefined ) {	// 上次没有选中---第一次加载
					if ( str_tempFirstTid != '' ) {	// 拿第一个终端
						str_tempNodeId = str_tempFirstTid;
					} else {
						str_tempNodeId = str_groupFirstId;
					}
				} else {
					str_tempNodeId = str_checkedNodeId;
				}
				if ( fn_lastinfoCompare(obj_newData) ) {
					obj_oldData = obj_newData;
					dlf.fn_loadJsTree(str_tempNodeId, str_html);
				}
				// autocomplete
				$('#txtautoComplete').autocomplete({
					source: arr_autoCompleteData,
					select: function(event, ui) {
						var str_tid = ui.item.value,
							obj_itemLi = $('.j_carList a[tid='+ str_tid +']'),
							str_crntTid = $('.j_leafNode a[class*=jstree-clicked]').attr('tid');

						$('#txtautoComplete').val( ui.item.label);
						if ( str_crntTid == str_tid ) {
							return false;
						}
						dlf.fn_loadJsTree(obj_itemLi.attr('id'), str_html);
						dlf.fn_switchCar(str_tid, obj_itemLi);
						return false;
					}
				});	// 自动完成 初始化
				// 点击查询按钮触发自动搜索功能
				$('#autoSearch').unbind('click').click(function() {
					$('#txtautoComplete').autocomplete('search');
				});				
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
			}
		},
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
}
/**
* 对比两次lastinfo的数据是否一致，不一致重新加载树
*/
function fn_lastinfoCompare(obj_newData) {
	var n_newDataLen = obj_newData.n_gLen,
		n_oldDataLen = obj_oldData.n_gLen, 
		arr_newGids = obj_newData.gids.split(','),
		arr_newTids = obj_newData.tids,
		arr_oldTids = obj_oldData.tids,
		str_gids = obj_oldData.gids,
		str_tids = obj_oldData.tids;
	
	// obj_newData = {'gids': str_groupIds, 'tids': arr_tids, 'n_gLen': n_groupLength};
	// valid len 
	if ( n_newDataLen != n_oldDataLen ) {
		return true;
	}
	// valid gids
	for ( var gid in arr_newGids ) {
		var str_gid = arr_newGids[gid];
		
		if ( str_gid != '' ) {
			if ( str_gids.search(str_gid) == -1 ) {
				return true;
			}
		}
	}
	// valid tids
	for ( var gid in arr_newTids ) {
		var str_tid = arr_newTids[gid], 
			str_oldTid = arr_oldTids[gid], 
			arr_newStrTids = str_tid.split(',');
		
		for ( var jTid in arr_newStrTids ) {
			var str_jTid = arr_newStrTids[jTid];
		
			if ( !str_oldTid  ) {
				return true;
			}
			if ( str_jTid != '' ) {
				if ( str_oldTid.search(str_jTid) == -1 ) {
					return true;
				}
			}
			
		}
	}
	return false;
}

/**
* 新建组
*/
function fn_createGroup(cid, str_name, obj_target) {
	var obj_param = {'name': str_name, 'cid': cid};
	
	$.post_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status == 0 ) {
			obj_target.attr('groupId', data.gid).addClass('groupNode');
		}
	});
}

/**
* 重命名组
*/
function fn_renameGroup(gid, str_name, node) {
	var obj_param = {'name': str_name, 'gid': gid};

	$.put_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			$.jstree.rollback(node);
		}
	});
}

/**
* 删除组
*/
function fn_removeGroup(gid, node) {
	var str_param = gid;
	
	$.delete_(GROUPS_URL + '?ids=' + str_param, '', function (data) {
		if ( !data.status == 0 ) {
			$.jstree.rollback(node);
		}
	});
}

/**
* 拖拽组
*/
function fn_moveGroup(arr_tids, n_newGroupId, node) {
	var obj_param = {'tids': arr_tids, 'gid': n_newGroupId}

	$.post_(GROUPTRANSFER_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			
		}
	});
}

/**
* 重命名集团名称 
*/
function fn_renameCorp(cid, str_name, node) {
	var obj_param = {'name': str_name, 'cid': cid};
	$.put_(CORP_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			$.jstree.rollback(node);
		}
	});
}

/**
* 新建终端
*/
function fn_initCreateTerminal(obj_node, str_groupId) {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#cTerminalWrapper')); // 新增终端dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化报警查询选择时间
	*/
	$('#hidGroupId').val(str_groupId);	// 保存groupId
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_begintime'), 
		obj_endTime = $('#c_endtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_begintime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_endtime\')}', qsEnabled: false});
	}).val(str_nowDate);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_endtime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_begintime\')}', qsEnabled: false});
	}).val(str_nextYearDate);	
	
	$('.j_corpData').val('');
	$('#hidTMobile').val('');
}

/**
* 保存终端
*/
window.dlf.fn_cTerminalSave = function() {
	var str_tmobile = $('#c_tmobile').val(),
		str_umobile = $('#c_umobile').val(),
		str_beginTime = $('#c_begintime').val(),
		str_endTime = $('#c_endtime').val(),
		str_cnum = $('#c_cnum').val(),
		str_ctype = parseInt($('#c_type').val()),
		str_color = $('#c_color').val(),
		str_brand = $('#c_brand').val(),
		n_groupId = parseInt($('#hidGroupId').val()),
		str_email = '',
		str_address = '',
		str_uname = '',
		obj_corpData = {};
		
	obj_corpData['tmobile'] = str_tmobile;
	obj_corpData['group_id'] = n_groupId;
	obj_corpData['umobile'] = str_umobile;
	obj_corpData['begintime'] = dlf.fn_changeDateStringToNum(str_beginTime + ' 00:00:00' );
	obj_corpData['endtime'] = dlf.fn_changeDateStringToNum(str_endTime + ' 23:59:59' );
	obj_corpData['cnum'] = str_cnum;
	obj_corpData['ctype'] = str_ctype;
	obj_corpData['ccolor'] = str_color;
	obj_corpData['cbrand'] = str_brand;
	obj_corpData['email'] = str_email;
	obj_corpData['address'] = str_address;
	obj_corpData['uname'] = str_uname;
	dlf.fn_jsonPost(TERMINALCORP_URL, obj_corpData, 'cTerminal', '终端信息保存中');
}
// 获取下一年的时间
function fn_getNextYear(str_nowDate) {
	var date = new Date(str_nowDate);
	date.setYear(date.getFullYear()+1);
	return date.getTime();
}

/**
* 修改终端
*/
function fn_initEditTerminal(str_tid) {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#cTerminalEditWrapper')); // 新增终端dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_editbegintime'), 
		obj_endTime = $('#c_editendtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_editbegintime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_editendtime\')}', qsEnabled: false});
	}).val(str_nowDate);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_editendtime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_editbegintime\')}', qsEnabled: false});
	}).val(str_nextYearDate);	
	$('.j_cterminalEdit').val('');
	$.get_(TERMINALCORP_URL + '?tid=' + str_tid, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.res,
				str_btime = dlf.fn_changeNumToDateString(obj_data.begintime * 1000, 'ymd'),
				str_etime = dlf.fn_changeNumToDateString(obj_data.endtime * 1000, 'ymd'),
				str_cnum = obj_data.cnum,
				str_type = obj_data.ctype,
				str_color = obj_data.ccolor,
				str_brand = obj_data.cbrand;
			
			$('.j_tmobile').html(obj_data.tmobile);
			$('.j_umobile').html(obj_data.umobile);
			$('#c_editbegintime').val(str_btime).data('c_editbegintime', str_btime);
			$('#c_editendtime').val(str_etime).data('c_editendtime', str_etime);
			$('#c_editcnum').val(str_cnum).data('c_editcnum', str_cnum);;
			$('#c_editctype').val(str_type).data('c_editctype', parseInt(str_type));
			$('#c_editccolor').val(str_color).data('c_editccolor', str_color);;
			$('#c_editcbrand').val(str_brand).data('c_editcbrand', str_brand);;
			$('#hidTid').val(str_tid);
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 4000); // 查询状态不正确,错误提示
		}
	});
}

/**
* 编辑保存终端
*/
window.dlf.fn_cEditTerminalSave = function() {
	var n_num = 0,
		obj_terminalData = {};
	$('.j_cterminalEdit').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
			
		if ( str_val != str_data ) {
			str_id = str_id.substr(6, str_id.length);
			if ( str_id == 'endtime' ) {
				str_val = dlf.fn_changeDateStringToNum(str_val + ' 23:59:59' );
			} else if ( str_id == 'begintime' ) {
				str_val = dlf.fn_changeDateStringToNum(str_val + ' 00:00:00' );
			}
			obj_terminalData[str_id] = str_val;
		}
	});
	
	for(var param in obj_terminalData) {	// 我的资料中修改项的个数
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		obj_terminalData['tid'] = $('#hidTid').val();
		dlf.fn_jsonPut(TERMINALCORP_URL, obj_terminalData, 'cTerminalEdit', '终端信息保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 删除终端
*/
function fn_removeTerminal(tid, node) {
	var str_param = tid;
	
	$.delete_(TERMINALCORP_URL + '?ids=' + str_param, '', function (data) {
		if ( !data.status == 0 ) {
			$.jstree.rollback(node);
		}
	});
}

/**
* 初始化告警统计
*/
window.dlf.fn_initStatics = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#staticsWrapper')); // 新增终端dialog显示
	/**
	* 初始化报警查询选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_eventbegintime'), 
		obj_endTime = $('#c_eventendtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_eventbegintime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_eventendtime\')}', qsEnabled: false});
	}).val(str_nowDate + ' 00:00:00');
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_eventendtime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_eventbegintime\')}', qsEnabled: false});
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(new Date(), 'sfm'));
	
	$('#staticsTableHeader').nextAll().remove();	//清除页面数据
	n_pageNum = 0;
	pagecnt = -1;
	/** 
	* 上一页按钮 下一页按钮
	*/
	var obj_prevPage = $('#prevPage'), 
		obj_nextPage = $('#nextPage'), 
		obj_pageContainer = $('#staticsPage'),
		obj_currentPage = $('#currentPage'),
		obj_search = $('#staticsBtn');
		
	obj_search.show();
	obj_pageContainer.hide();
	/** 
	* 绑定按钮事件
	*/
	dlf.fn_setItemMouseStatus(obj_search, 'pointer', new Array('cx', 'cx2'));
	dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage2', 'prevPage1'));
	dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage2', 'nextPage1'));
	/**
	* 上下页事件绑定
	*/
	obj_prevPage.click(function() {
		if ( n_pageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_pageNum+1);
		fn_searchStatics(n_pageNum);
	});
	obj_nextPage.click(function() {
		if ( n_pageNum >= pagecnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_pageNum+1);
		fn_searchStatics(n_pageNum);
	});
	
	obj_search.unbind('click').bind('click', function() {	// 告警记录查询事件
		pagecnt = -1;
		n_pageNum = 0;
		fn_searchStatics(n_pageNum);
	});
}

/**
* 查询统计
*/
function fn_searchStatics(n_num) {
	var n_startTime = $('#c_eventbegintime').val(), // 用户选择时间
		n_endTime = $('#c_eventendtime').val(), // 用户选择时间
		n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
		n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
		n_category = $('#category').val(), 
		obj_staticsParam = {'start_time': n_bgTime, 'end_time': n_finishTime, 
				'pagenum': n_pageNum, 'pagecnt': pagecnt};
	
	dlf.fn_jNotifyMessage('告警统计查询中...', 'message', true);
	
	$.post_(STATICS_URL, JSON.stringify(obj_staticsParam), function(data) {	// 获取告警记录信息
		if ( data.status == 0 ) {  // success
			var obj_prevPage = $('#prevPage'), 
				obj_nextPage = $('#nextPage'),
				n_eventDataLen = 0,
				str_tbodyText = '';
				
			$('#staticsTableHeader').nextAll().remove();	//清除页面数据
			pagecnt = data.pagecnt;
			arr_staticsData = data.res;
			n_eventDataLen = arr_staticsData.length; 	//记录数
			
			if ( n_eventDataLen > 0 ) {	// 如果查询到数据
				$('#staticsPage').show(); //显示分页
				if ( pagecnt > 1 ) {	// 总页数大于1 
					if ( n_num > 0 && n_num < pagecnt-1 ) {  //上下页都可用 
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
					} else if ( n_num >= pagecnt-1 ) {	//下一页不可用						
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
					} else {	//上一页不可用					
						dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
					}				
				} else {	//总页数小于1  上下页都不可用
					dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
					dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
				}
				
				if ( n_num == 0 ) {	// 只有在点击查询按钮时才重新显示总页数
					$('#pageCount').text(data.pagecnt); //总页数
					$('#currentPage').html('1');	//当前页数
				}
				for(var i = 0; i < n_eventDataLen; i++) {
					var obj_statics = arr_staticsData[i], 
						str_alias = obj_statics.alias,	// 终端手机号
						str_illegalmove = obj_statics.illegalmove + '次',	// 非法移动
						str_sos = obj_statics.sos + '次',	// sos
						str_illegashake =  obj_statics.illegashake + '次', // 震动
						str_heartbeat_lost = obj_statics.heartbeat_lost + '次',	// 心跳
						str_powerlow = obj_statics.powerlow + '次';	// 低电
						//str_html = str_illegalmove + str_sos + str_illegashake + str_heartbeat_lost + str_powerlow;
					
					/**
					* 拼接table
					*/
					str_tbodyText+= '<tr>';
					str_tbodyText+= '<td>'+ str_alias +'</td>';	// 终端
					str_tbodyText+= '<td>'+ str_illegalmove +'</td>';	// 告警详情
					str_tbodyText+= '<td>'+ str_sos +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_illegashake +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_heartbeat_lost +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_powerlow +'</td>';	// 告警详情				
					str_tbodyText+= '</tr>';
				}
				$('#staticsTableHeader').after(str_tbodyText);
				/** 
				* 初始化奇偶行
				*/
				$('.dataTable tr').mouseover(function() {
					$(this).css('background-color', '#FFFACD');
				}).mouseout(function() {
					$(this).css('background-color', '');
				});		
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			} else {
				$('#staticsPage').hide(); //显示分页
				dlf.fn_jNotifyMessage('该时间段没有告警记录，请选择其它时间段。', 'message', false, 6000);
			}
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip('event');
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);	
		}
	},
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 验证终端手机号
*/
window.dlf.fn_checkTMobile = function(str_tmobile) {
	$.get_(CHECKMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			$('#hidTMobile').val('1');
			dlf.fn_jNotifyMessage('终端手机号已存在。', 'message', false, 5000);
			return;
		} else {
			$('#hidTMobile').val('');
		}
	});
}
/**
* 验证集团名是否重复
*/
window.dlf.fn_checkCName = function(str_cname) {
	$.get_(CHECKCNAME_URL + '/' + str_cname, '', function(data){
		if ( data.status != 0 ) {
			$('#hidCName').val('1');
			dlf.fn_jNotifyMessage('集团名称已存在。', 'message', false, 5000);
			return;
		} else {
			$('#hidCName').val('');
		}
	});
}
})();