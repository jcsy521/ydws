/**
* 集团用户操作方法
* obj_carsData: 存储lastinfo中所有定位器的信息
* str_currentTid: 上次lastinfo的选中定位器tid
* arr_autoCompleteData: autocomplete 查询数据
* b_createTerminal： 标记是新增定位器操作 方便switchcar到该新增车辆
* n_onlineCnt：在线终端总数
* n_offlineCnt：离线终端总数
* arr_treeNodeChecked: 树中所有选中的终端
* arr_submenuGroups: 移动至组的所有组名
* obj_tracePolylines: 甩尾轨迹线
* arr_tracePoints: 甩尾数据点
*/
var obj_carsData = {},
	str_currentTid = '',
	arr_autoCompleteData = [],
	b_createTerminal = false,
	n_onlineCnt = 0,
	n_offlineCnt = 0, 
	arr_treeNodeChecked = [],
	arr_submenuGroups = [],
	obj_tracePolylines = {},
	arr_tracePoints = [];
	
(function() {

/**
*  创建右键菜单，设置每个节点的菜单右键菜单
*/
function customMenu(node) {
	var obj_node = $(node),
		obj_currentGroup = obj_node.parent().siblings('a'),
		str_currentGroupName = obj_currentGroup.attr('title'),	// 当前定位器所在组名
		str_groupId = obj_currentGroup.attr('groupId'),	// 当前所在组的组ID
		str_userType = $('.j_body').attr('userType'),	// 用户类型
		items = null,		// 菜单的操作方法
		submenuItems = {},	// 二级菜单
		subDefendItems = {},	// 批量设防撤防二级菜单
		renameLabel = '',	// 重命名lable
		createLabel = '',	// 新建lable
		batchImportDeleteLabel = '',	// 批量导入
		batchDeleteLabel = '',	// 批量删除
		moveToLabel = '',	// 移动至
		eventLabel = '',	// 告警查询
		terminalLabel = '',	// 参数设置
		deleteLabel = '',	// 删除lable
		batchDefendLabel = '',	// 批量设防*撤防
		batchRegionLabel = '',	// 批量设置电子围栏
		singleDeleteLabel = '',	// 删除单个定位器
		singleCreateLabel = '',	// 单个定位器的添加
		singleDefendLabel = '',	// 单个定位器设防撤防
		realtimeLabel = '',	// 单个定位器实时定位
		trackLabel = '',	// 单个定位器轨迹查询
		staticsLabel = '',	// 单个定位器统计报表
		bindLineLabel = '', // 绑定线路
		bindRegionLabel = '', // 绑定围栏
		batchTrackLabel = '',	// 开启追踪
		batchCancleTrack = '',	// 取消追踪
		str_bizCode = $('#hidBizCode').val(),	// 当前的业务
		obj_alarmAndDelay = $('.j_alarm, .j_delay'),
		b_trackStatus = $('#trackHeader').is(':visible');	// 轨迹是否打开着
	
	if ( obj_node.hasClass('j_corp') ) {		// 集团右键菜单
		renameLabel = '重命名集团';
		createLabel = '新建分组';
		deleteLabel = '删除集团';
	} else if (obj_node.hasClass('j_group')) {	// 组右键菜单
		renameLabel = '重命名组';
		deleteLabel = '删除分组';
		singleCreateLabel = '添加单个定位器';
		batchImportDeleteLabel = '批量导入/删除';
		batchDeleteLabel = '批量删除定位器';
		batchDefendLabel = '批量设防/撤防';
		batchRegionLabel = '批量绑定围栏';
		batchTrackLabel = '批量开启追踪';
		batchCancleTrackLabel = '批量取消追踪';
	} else {						// 定位器右键菜单
		terminalLabel = '参数设置';
		singleDeleteLabel = '删除定位器';
		realtimeLabel = '实时定位';
		trackLabel = '轨迹查询';
		eventLabel = '告警查询';
		moveToLabel = '移动定位器';
		singleDefendLabel = '设防/撤防';
		staticsLabel = '里程统计';
		bindLineLabel = '绑定/解绑线路';
		bindRegionLabel = '绑定围栏';
	}
	// 定位器的移动至菜单项
	
	for ( var i in arr_submenuGroups ) {
		var obj_group = arr_submenuGroups[i],
			str_groupName = obj_group.groupName,
			str_groupId = obj_group.groupId;
		
		if ( str_currentGroupName != str_groupName ) {
			submenuItems['moveToGroup' + str_groupId ] = fn_createSubMenu(obj_group);
		}
	}
	// 右键菜单执行的操作
	items = {
		"create" : {		// 新增分组
			"label" : createLabel,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_corp') ) {
					this.create();
				} else {
					return false;
				}	
			}
		},
		"singleCreate": {		// 单个定位器添加
			"label": singleCreateLabel,
			"action": function(obj) {
				var obj_this = $(obj).eq(0);
				
				fn_initCreateTerminal('', obj_this.children('a').eq(0).attr('groupId'));
				return false;
			}
		},
		"realtime": {
			"label" : realtimeLabel,
			"action" : function(obj) {	// 实时定位初始化				
				dlf.fn_currentQuery();
			}
		},
		"track": {
			"label" : trackLabel,
			"action" : function(obj) {	// 轨迹查询初始化
				if ( b_trackStatus ) {
					return;
				}
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();	
				dlf.fn_initTrack();
			}
		},
		"event": {
			"label" : eventLabel,
			"action" : function(obj) {	// 告警查询初始化
				// 查询单个终端告警
				dlf.fn_eachCheckedNode('.j_leafNode');
				// 将之前的checked状态填充 
				var n_treeNodeCheckLen = arr_treeNodeChecked.length;
				
				if ( n_treeNodeCheckLen > 0 ) {
					for ( var i = 0; i < n_treeNodeCheckLen; i++ ) {
						$('#corpTree').jstree('uncheck_node', arr_treeNodeChecked[i]);
					}
				}
				$('#corpTree').jstree('check_node', $(obj).eq(0));
				dlf.fn_initRecordSearch('eventSearch');
			}
		},
		"bindLine": {
			"label" : bindLineLabel,
			"action" : function(obj) {	// 绑定线路	
				if ( b_trackStatus ) {	// 如果轨迹打开 要重启lastinfo
					dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询,不操作lastinfo
				}
				dlf.fn_routeLineBindEvent();
			}
		},
		/*
		"region": {
			"label" : '电子围栏',
			"action" : function(obj) {	// 终端右键菜单 电子围栏 kjj add  2013-07-10
				obj_alarmAndDelay.hide();
				dlf.fn_initRegion();
			}
		},*/
		"bindRegion": {
			"label" : bindRegionLabel,
			"action" : function(obj) {	// todo 
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();
				dlf.fn_initBindRegion();
			}
		},
		"batchRegion" : {
			"label" : batchRegionLabel,
			"action": function (obj) { // 批量设置电子围栏
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();
				dlf.fn_initBatchRegions(obj);
			}
		},
		"terminalSetting": {	// 参数设置
			"label" : terminalLabel,
			"action" : function (obj) {
				dlf.fn_initCorpTerminal($(obj).children('a').eq(0).attr('tid'));
				return false;
			}
		},
		"defend": {	// 单个定位器设防撤防
			"label" : singleDefendLabel,
			"action" : function (obj) {
				dlf.fn_defendQuery(obj.children('a').attr('alias'));
			}
		},
		"batchImportDelete": {	// 批量导入定位器操作菜单
			"label" : batchImportDeleteLabel,
			"submenu": {
				'batchImport': {
					"label" : "批量导入定位器",
					"action" : function (obj) {
						// todo 批量导入定位器操作
						var obj_batch = obj.children('a'),
							n_gid = obj_batch.attr('groupid'),
							str_gname = obj_batch.attr('title');
							
						fn_initBatchImport(n_gid, str_gname);
						return false;
					}
				},
				'batchDelete': {
					"label" : "批量删除定位器",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '删除');
					}
				}
			}
		},
		"batchDefend" : {
			"label" : batchDefendLabel,
			"submenu": {
				'defend0': {
					"label" : "批量设防",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '设防');
					}
				},
				'defend1': {
					"label" : "批量撤防",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '撤防');
					}
				}
			}
		},
		"batchTrack" : {
			"label" : "批量追踪",
			"submenu": {
				'batchTrack0': {
					"label" : "开启",
					"action" : function (obj) {
						fn_batchOpenTrack(obj, 'open');
					}
				},
				'batchTrack1': {
					"label" : "关闭",
					"action" : function (obj) {
						fn_batchOpenTrack(obj, 'close');
					}
				}
			}
		},
		/*		
		"batchTrack" : {
			"label" : "批量开启追踪",
			"action": function (obj) { // 批量追踪定位器
				
			}
		},
		"batchCancleTrack": {
			"label" : "批量取消追踪",
			"action": function (obj) { // 批量追踪定位器
				
			}		
		},*/
		"rename" : {
			"label" : renameLabel,
			"action" : function(obj) {
				var obj_node = $(obj).children('a'),
					str_class = obj_node.attr('class');
				
				this.rename(obj);
				// kjj add in 2013.10.10 重命名集团名称和分组名称时，名称>20不允许输入
				$('.jstree-rename-input').unbind('keydown').bind('keydown', function() {
					var obj_this = $(this),
						str_val = obj_this.val();
					
					if ( str_val.length > 20 ) {
						obj_this.val(str_val.substr(0, 20));
					}
				});
				$('.jstree-rename-input').val($(obj).children('a').attr('title'));
			}
		},
		/*"moveTo": {
			"label" : moveToLabel,
			"submenu": submenuItems
		},*/
		"moveTerminal": {
			"label" : moveToLabel,
			"submenu": submenuItems
		},
		"remove" : {
			"label" : deleteLabel,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_group') ) {	// 删除组
					// 判断是否有定位器 
					var n_terminalLength = obj_this.children('ul').length,
						str_gid = obj_this.children('a').attr('groupid');
						
					if ( n_terminalLength > 0 ) {
						$('#vakata-contextmenu').hide();	// 隐藏右键菜单
						alert('该分组下有定位器不能删除.');
						return;
					} else {
						fn_removeGroup(obj);
						return false;
					}
				}
			}
		},
		"singleDelete" : {
			"label" : singleDeleteLabel,
			"action" : function (obj) {
				fn_removeTerminal(obj);
				return false;
			}
		},
		"statics": {
			"label": staticsLabel,
			"action" : function (obj) {
				dlf.fn_initRecordSearch('singleMileage');
			}
		}
	};
	// 终端右键菜单菜单
   if ( obj_node.hasClass('j_leafNode') ) {
		delete items.create;
		delete items.singleCreate;
		delete items.batchImportDelete;
		delete items.rename;
		delete items.batchDefend;
		delete items.batchRegion;
		delete items.remove;
		delete items.batchTrack;
   }
   // 集团右键菜单删除菜单
   if ( obj_node.hasClass('j_corp')  ) {
		delete items.singleCreate;
		delete items.remove;
		delete items.batchImportDelete;
		// delete items.moveTo;	
		delete items.moveTerminal;
		delete items.event;
		delete items.terminalSetting;
		delete items.batchDefend;
		delete items.batchRegion;
		delete items.defend;
		delete items.realtime;
		delete items.track;
		delete items.statics;
		delete items.singleDelete;
		delete items.bindLine;
		delete items.bindRegion;
		delete items.region;
		delete items.batchTrack;
   }
   if ( obj_node.hasClass('j_group') ) {
		delete items.create;
		//delete items.moveTo;
		delete items.moveTerminal;
		delete items.event;
		delete items.terminalSetting;
		delete items.defend;
		delete items.realtime;
		delete items.track;
		delete items.statics;
		delete items.singleDelete;
		delete items.bindLine;
		delete items.bindRegion;
		delete items.region;
   }
   if ( str_userType == USER_OPERATOR ) {	// 操作员屏蔽右键	
		delete items.create;
		delete items.singleCreate;
		delete items.batchImportDelete;
		delete items.remove;
		delete items.rename;
		
		delete items.bindLine;
		delete items.singleDelete;
		delete items.moveTerminal;	// 暂时隐藏操作员的移动至功能
		
		/*
		delete items.batchRegion;
		delete items.batchDefend;
		delete items.moveTo;
		delete items.event;	
		delete items.terminalSetting;
		delete items.defend;
		delete items.statics;
		delete items.bindRegion;
		delete items.bindRegion;*/
   }
   if ( str_bizCode != 'znbc' ) {	// 如果集团业务不是智能班车业务的话  没有绑定线路功能
		delete items.bindLine;
   }
   return items;
}

/**
* 批量操作的数据验证：批量删除、批量设防撤防 (判断是否选中的是定位器)
*/
function fn_batchOperateValidate(obj, str_msg) {
	var obj_currentGroupChildren = obj.children('ul'),
		str_gname = obj.children('a').text();	// 组名
	
	//  批量删除选中定位器操作
	if ( obj_currentGroupChildren.length <= 0 ) {	// 没有定位器，不能批量删除
		dlf.fn_jNotifyMessage('该组下没有定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else if ( obj.hasClass('jstree-unchecked') ) {	// 要删除定位器的组没有被选中
		dlf.fn_jNotifyMessage('没有选中要'+ str_msg +'的定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else {
		var arr_tids = [],
			arr_dataes = [],
			obj_params = {};
		// 当前组下选中的tid
		obj_currentGroupChildren.children('li').each(function() {
			var obj_checkedTerminal = $(this),
				obj_terminalALink = obj_checkedTerminal.children('a'),
				b_isChecked = obj_checkedTerminal.hasClass('jstree-checked'),
				str_tid = obj_terminalALink.attr('tid'),
				str_alias = obj_terminalALink.attr('alias'),	// tnum
				str_tmobile = obj_terminalALink.attr('title');	// tmobile
				//obj_carsData = $('.j_carList').data('carsData');	// todo 
			
			if ( b_isChecked ) {
				arr_tids.push(str_tid);
				arr_dataes.push({'alias': dlf.fn_encode(str_alias), 'tmobile': str_tmobile, 'tid': str_tid, 'mennual_status': obj_carsData[str_tid].mannual_status});
			}
			obj_params['tids'] = arr_tids;
			obj_params['characters'] = arr_dataes;
			obj_params['gname'] = str_gname;
		});
		str_msg == '删除' ? fn_batchRemoveTerminals(obj_params) : dlf.fn_initBatchDefend(str_msg, obj_params);
	}
}

/**
* 批量开启定位器
* obj: 操作的组对象
* str_operation: open:开启追踪  close: 取消追踪
*/
function fn_batchOpenTrack(obj, str_operation) {
	var obj_currentGroupChildren = obj.children('ul'),
		str_gname = obj.children('a').text();	// 组名
	
	//  批量删除选中定位器操作
	if ( obj_currentGroupChildren.length <= 0 ) {	// 没有定位器，不能批量删除
		dlf.fn_jNotifyMessage('该组下没有定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else if ( obj.hasClass('jstree-unchecked') ) {	// 要删除定位器的组没有被选中
		dlf.fn_jNotifyMessage('没有选中要操作的定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else {
		var arr_tids = [],
			arr_dataes = [],
			obj_params = {};
		// 当前组下选中的tid
		obj_currentGroupChildren.children('li').each(function() {
			var obj_checkedTerminal = $(this),
				obj_terminalALink = obj_checkedTerminal.children('a'),
				b_isChecked = obj_checkedTerminal.hasClass('jstree-checked'),
				str_tid = obj_terminalALink.attr('tid'),
				obj_currentMarker = obj_selfmarkers[str_tid],
				str_alias = obj_terminalALink.attr('alias'),	// tnum
				str_tmobile = obj_terminalALink.attr('title'),	// tmobile
				str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
			
			if ( b_isChecked ) {
				if ( str_operation == 'open' && str_actionTrack != 'yes' && obj_currentMarker ) {	// 选中终端没有开启追踪
					arr_tids.push(str_tid);
				} else if ( str_operation == 'close' && str_actionTrack != 'no' && str_actionTrack != '' && obj_currentMarker ) {	// 选中终端 取消追踪
					arr_tids.push(str_tid);
				}
				arr_dataes.push({'alias': dlf.fn_encode(str_alias), 'tmobile': str_tmobile, 'tid': str_tid, 'track': str_actionTrack});
			}
		});
		if ( arr_tids.length <= 0 ) {
			dlf.fn_jNotifyMessage('您选中的定位器都'+ ( str_operation == 'open' ? '已' : '未' ) +'开启追踪。', 'message', false, 3000); // 执行操作失败，提示错误消息
			return false;
		}
		obj_params['tids'] = arr_tids;
		obj_params['characters'] = arr_dataes;
		obj_params['gname'] = str_gname;
		dlf.fn_initOpenTrack(str_operation, obj_params);
	}
}

/**
* 批量开启追踪数据回显
*/
window.dlf.fn_initOpenTrack  = function(str_operation, obj_params) {
	dlf.fn_dialogPosition('batchTrack');	// 设置dialog的位置
	
	var arr_dataes = obj_params.characters;
		obj_table = $('.batchTrackTable tbody'),
		obj_head = $('.batchTrackTable thead th');
	
	obj_table.html('');	// 清空表格数据
	for ( var i = 0; i < arr_dataes.length; i++ ) {
		var obj = arr_dataes[i],
			str_html = '',
			str_trackStatus = obj.track,
			str_track = '';
		
		str_html = '<tr><td>'+ obj.alias +'</td><td>'+ obj.tmobile +'</td>';
		if ( str_trackStatus == 'yes' ) {
			str_track = '已开启';
		} else {
			str_track = '未开启';
		}
		str_html += '<td>'+ str_track + '</td>';
		str_html += '</tr>';
		obj_table.append(str_html);	// 填充要删除的数据
	}
	obj_head.html(obj_params.gname);	// 表头显示组名
	
	var obj_defend = {},
		str_track = str_operation == 'open' ? '开启追踪' : '取消追踪';
	
	$('.j_batchTrack').val('批量' + str_track).unbind('click').bind('click', function() {
		dlf.setTrack(obj_params.tids);
	});
}

/**
* 生成二级菜单项
* obj_group: 二级菜单项要显示的内容对象
*/
function fn_createSubMenu(obj_group) {
	var str_groupName = obj_group.groupName,
		str_groupId = obj_group.groupId;
		
	return {
		"label": str_groupName, 
		"action": function(obj) {
			// 移动至组的方法实现
			var str_moveTid = obj.children('a').attr('tid');
			fn_moveGroup([str_moveTid], str_groupId, '', obj.attr('id'));
		}
	}
}

/**
* jstree初始化，右键菜单事件处理、树加载完成事件处理、节点单击事件处理、双击事件处理
* str_checkedNodeId：默认要选中的节点id
* str_html：动态生成的树的html
* dnd: drag
* contextmenu: right-menu
* types: node icon
* crrm: create、remove、rename等
*/
window.dlf.fn_loadJsTree = function(str_checkedNodeId, str_html) {
	$('#corpTree').jstree({
		"plugins": [ "themes", "html_data", "ui", "contextmenu",'crrm', "types", 'dnd', 'checkbox'],
		'core': {
			'strings': {
				'new_node': '新建组'
			}
		},
		'html_data': {
			'data': str_html
		},
		"contextmenu" : {
			'items': customMenu,
			'select_node': true
		},
		'themes': {
			'theme': 'classic',
			'icons' : true
		},
		'ui': {
			'initially_select': str_checkedNodeId	// 设置默认选中的节点
		},
		"crrm" : {
			"move": {
				"check_move" : function (m) {
					var obj_currentNode = m.o,
						p = this._get_parent(obj_currentNode);
					
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
						return true;
					}
					return false;
				}
			}
		}
	}).bind('move_node.jstree', function(e, data) {
		var obj_currentNode = data.rslt.o,
			obj_currentA = obj_currentNode.children('a').eq(0),
			str_tid = obj_currentA.attr('tid'),
			obj_target = data.rslt.np,
			str_groupId = $(obj_target).children('a').attr('groupid'),
			arr_tids = [];
			if ( str_tid ) {	// 只有终端才可以移动到组
				arr_tids.push(str_tid);
				fn_moveGroup(arr_tids, str_groupId, data.rlbk);
			}
	}).bind('create.jstree', function(e, data) {
		var obj_rslt = data.rslt,
			obj_rollBack = data.rlbk,
			str_newName = obj_rslt.name,
			str_cid = $(obj_rslt.parent).children('a').attr('corpid') || $('.j_body').attr('cid');
		
		fn_createGroup(str_cid, str_newName, obj_rollBack, obj_rslt.obj);
	}).bind('rename.jstree', function(e, data) {	// 重命名
		var	obj_rslt = data.rslt,
			obj_currentNode = $(obj_rslt.obj[0]),
			obj_current = obj_currentNode.children('a').eq(0),
			str_newName = obj_rslt.new_name,
			obj_rlbk = data.rlbk,
			b_flag = obj_currentNode.hasClass('j_leafNode');

		if ( str_newName == data.rslt.old_name && !b_flag ){	// 如果新名称和旧名称相同 不操作
			return;
		}
		if ( obj_currentNode.hasClass('j_group') ) {	// 重命名组	
			fn_renameGroup(obj_current.attr('groupid'), str_newName, obj_rlbk);
		} else if ( obj_currentNode.hasClass('j_corp') ) {	// 重命名集团
			var str_cid = obj_current.attr('corpid') || $('.j_body').attr('cid');
			
			fn_renameCorp(str_cid, str_newName, obj_rlbk)
		}
	}).bind('loaded.jstree', function(e, data) {	// 树节点加载完成事件
		data.inst.open_all(-1);	// 默认展开所有的节点
		dlf.fn_setCorpIconDiffBrowser();
		// 更新定位器总数
		fn_updateTerminalCount();
		// 循环所有定位器 找到当前定位器并更新车辆信息
		var b_loop = true,
			n_num = 0,
			n_pointNum = 0,
			arr_locations = [];
			
		for ( var index in obj_carsData ) {
			n_num ++;
		}
		if ( n_num > 0 ) {
			for ( var param in obj_carsData ) {
				var obj_car = obj_carsData[param],
					obj_trace = obj_car.trace_info,	// 甩尾数据
					obj_track = obj_car.track_info,	// 开启追踪点数据
					n_enClon = obj_car.clongitude,
					n_enClat = obj_car.clatitude,
					n_lon = obj_car.longitude,
					n_lat = obj_car.latitude,
					n_clon = n_enClon/NUMLNGLAT,	
					n_clat = n_enClat/NUMLNGLAT;
				
				if ( n_lon != 0 && n_lat != 0 ) {
					if ( n_clon != 0 && n_clat != 0 ) {
						n_pointNum ++;
						arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
						obj_car.trace_info = obj_trace;
						obj_car.track_info = obj_track;
						dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
						if ( dlf.fn_isEmptyObj(obj_trace) ) {	// 生成甩尾数据
							obj_trace.tid = param;
						}
					} else {
						dlf.fn_translateToBMapPoint(n_lon, n_lat, 'lastposition', obj_car);	// 前台偏转 kjj 2013-09-27
					}
				}
			}
			if ( str_currentTid != undefined && str_currentTid != '' ) {
				if ( b_createTerminal ) {	// 如果是新建终端 发起switchCar
					var obj_newTerminal = $('#leaf_' + str_currentTid);
					
					dlf.fn_switchCar(str_currentTid, obj_newTerminal);
					data.inst.open_all(0); // -1 opens all nodes in the container
				} else {
					for(var param in obj_carsData) {
						var obj_carInfo = obj_carsData[param], 
							str_tid = param;
						
						if ( str_currentTid == str_tid || str_checkedNodeId.substr(5, str_checkedNodeId.length) == str_tid ) {	// 更新当前车辆信息
							dlf.fn_updateTerminalInfo(obj_carInfo);
							b_loop = false;
						}
					}
				}
			} else {	// 第一次发起switchCar启动lastinfo
				var obj_current = $('#' + data.inst.data.ui.to_select);
				if ( arr_locations.length > 0 ) {
					dlf.fn_caculateBox(arr_locations);
				}
				str_currentTid = str_checkedNodeId.substr(5, str_checkedNodeId.length);
				dlf.fn_switchCar(str_currentTid, obj_current);
			}
			fn_updateAllTerminalLogin();
			$('.groupNode').css('color', '#000');
			
		} else {	// 无终端 启动lastinfo
			dlf.fn_updateLastInfo();
			dlf.fn_initCarInfo();
		}
		// 如果无终端或终端都无位置  地图设置为全国地图
		if ( n_pointNum <= 0 ) {
			mapObj.setZoom(5);
		}
		// 将之前的checked状态填充 
		var n_treeNodeCheckLen = arr_treeNodeChecked.length;
		
		if ( n_treeNodeCheckLen > 0 ) {
			for ( var i = 0; i < n_treeNodeCheckLen; i++ ) {
				$('#corpTree').jstree('check_node', arr_treeNodeChecked[i]);
			}
			arr_treeNodeChecked = [];
		}
	}).bind('contextmenu.jstree', function(event, data) {	// 右键除当前定位器外其余都不被选中
		var obj_current = fn_nodeCurrentNode(event.target),
			obj_currentCarParent = $('.j_terminal[tid='+ str_currentTid +']').parent();
		
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				return;
			}
			$('#corpTree').jstree('uncheck_node.jstree', 'leafNode_'+ str_currentTid);
			// obj_currentCarParent.removeClass('jstree-checked');
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,   
		} else {
			obj_current.removeClass(JSTREECLICKED);
		}
	}).bind('click.jstree', function(event, data) {	// 选中节点事件
		var obj_current = fn_nodeCurrentNode(event.target);					
		
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				var obj_currentMarker = obj_selfmarkers[str_tid];				
				
					if ( obj_currentMarker ) {	// 2013-07-29 add 切换当前车 只打开吹出框
						var obj_position = obj_currentMarker.getPosition(),
							obj_infowindow = obj_currentMarker.selfInfoWindow;
						
						mapObj.setCenter(obj_position);
						if ( dlf.fn_isBMap() ) {
							obj_currentMarker.openInfoWindow(obj_infowindow);
						} else {
							obj_selfmarkers[str_tid].selfInfoWindow.open(mapObj, obj_position);	// 显示吹出框
						}
			    	}
				return;
			}
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,   
		} else {	// 集团或组	如果选中集团或组的话没有被选中的样式、上一次选中的定位器还被选中			
			$('.j_terminal[tid='+ str_currentTid +']').addClass(JSTREECLICKED);
			$('.groupCss').removeClass('groupCss');
			obj_current.removeClass(JSTREECLICKED).addClass('groupCss');
			return false;
		}
	}).bind('dblclick.jstree', function(event, data) {
		
		var obj_target = $(event.target),
			b_class = obj_target.hasClass('j_terminal'),
			str_tid = obj_target.attr('tid');

		if ( b_class ) {	// 双击定位器
			dlf.fn_initCorpTerminal(str_tid);
		} else {
			return false;
		}
	}).bind('check_node.jstree', function(obj) {
		// console.log(obj);	// 记住选中的
	});
}

/**
* jstree 的事件target对象获取
*/
function fn_nodeCurrentNode(target) {
	var str_nodeName = target.nodeName,
		obj_current = $(target),
		b_terminalClass = obj_current.hasClass('j_terminal');
					
	if ( str_nodeName == 'INS' ) {
		obj_current = $(target).parent();
		b_terminalClass = obj_current.hasClass('j_terminal');
	}
	obj_current.b_terminalClass = b_terminalClass;
	return obj_current;
}

/**
* 更新终端总数
* str_operation: add(新增定位器)、sub(删除定位器)
* num: 新增或删除定位器的个数
*/
function fn_updateTerminalCount(str_operation, num) {
	
	switch ( str_operation ) {
		case 'add':
			n_onlineCnt = n_onlineCnt + num;
			break;
		case 'sub':
			n_offlineCnt = n_offlineCnt - num;
			break;
		default:
			break;
	}
	// 更新定位器总数
	$('.carCount').html( n_onlineCnt + n_offlineCnt + '(全部)');
	$('.onlineCount').html(n_onlineCnt + '(在线)');
	$('.offlineCount').html(n_offlineCnt + '(离线)');
}

/**
* 集团用户 lastinfo
* b_isOpenInfowindow
*/
window.dlf.fn_corpGetCarData = function(b_isCloseTrackInfowindow) {
	var obj_current = $('.j_leafNode a[class*='+ JSTREECLICKED +']'),
		str_checkedNodeId = obj_current.attr('id'),	// 上一次选中车辆的id
		str_tempTid = '',
		b_flg = false,
		obj_param = {'lastinfo_time': -1},
		str_lastinfoTime = $('.j_body').data('lastinfo_time'),
		arr_tracklist = [],
		obj_tempCarsData = $('.j_carList').data('carsData');

	str_checkedNodeId = str_checkedNodeId == undefined ? 'leaf_' + str_currentTid : str_checkedNodeId;
	str_tempTid = str_checkedNodeId.substr(5, str_checkedNodeId.length);
	str_currentTid = obj_current.attr('tid');	// load.jstree时更新选中的车
	
	if ( dlf.fn_isEmptyObj(obj_carsData) ) {
		$('.j_terminal').each(function() {
			var str_tid = $(this).attr('tid'),
				str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
				
			if ( str_actionTrack == 'yes' ) {
				arr_tracklist.push({'track_tid': str_tid, 'track_time': obj_carsData[str_tid].timestamp});
			}
		});
	}
	if ( str_lastinfoTime ) {
		obj_param.lastinfo_time = str_lastinfoTime;
	}
	if ( arr_tracklist.length > 0 ) {
		obj_param.track_lst = arr_tracklist;
	}
	$.post_(CORP_LASTINFO_URL, JSON.stringify(obj_param), function (data) {	// 向后台发起lastinfo请求
		if ( data.status == 0 ) {
			var obj_corp = data.res,
				arr_groups = obj_corp.groups,	// all groups 
				n_groupLength = arr_groups.length,	// group length
				str_corpName = obj_corp.name,	// corp name
				str_tempCorpName = str_corpName,
				str_corpId = obj_corp.cid,		// corp id
				str_html = '<ul>',
				arr_groupIds = [], // 组ID组
				arr_tids = [], 	// 组下的tid组
				str_tempFirstTid = '',	// 默认第一个tid
				str_groupFirstId = '',	// 默认第一个groupid
				b_isHasTerminal = true,	// 是否有终端
				obj_newData = {},
				obj_tempSelfMarker = {};	// 临时存储最新的marker数据
				
			// $('.j_alarmTable').removeData('num');
			$('.j_body').attr('cid', str_corpId);	//  存储集团id防止树节点更新时 操作组 丢失cid	
			$('.j_body').data('lastinfo_time', data.res.lastinfo_time);	// 存储post返回的上次更新时间  返给后台
			n_onlineCnt = obj_corp.online,		// online count
			n_offlineCnt = obj_corp.offline;	// offline count
			
			if ( str_corpId && str_corpName ) {
				str_tempCorpName = str_corpName.length > 10 ? str_corpName.substr(0,10)+ '...' : str_corpName;
				str_html += '<li class="j_corp" id="treeNode_'+ str_corpId +'"><a title="'+ str_corpName +'" corpid="'+ str_corpId +'" class="corpNode" href="#">'+ str_tempCorpName +'</a>';
			}
			fn_updateTerminalCount();	// lastinfo 每次更新在线个数 2013-07-29 kjj add
			arr_autoCompleteData = [];
			arr_submenuGroups = [];
			if ( n_groupLength > 0 ) {
				str_html += '<ul>';
				str_groupFirstId = 'group_' + arr_groups[0].gid;
				
				obj_carsData = {};
				for ( var i = 0; i < n_groupLength; i++ ) {	// 添加组
					var obj_group = arr_groups[i],
						str_groupName = obj_group.name,
						n_groupNameLng = str_groupName.length,
						str_tempGroupName = n_groupNameLng>10 ? str_groupName.substr(0,10)+ '...' : str_groupName,
						str_groupId = obj_group.gid,
						obj_trackers = obj_group.trackers,
						arr_tempTids = []; //tid组
						//arr_tids = [];
					
					arr_submenuGroups.push({'groupId': str_groupId, 'groupName': str_groupName});
					str_html += '<li class="j_group" id="groupNode_'+ str_groupId +'"><a href="#" class="groupNode" groupId="'+ str_groupId +'" title="'+ str_groupName +'" id="group_'+ str_groupId +'">'+ str_tempGroupName +'</a>';
					
					if ( dlf.fn_isEmptyObj(obj_trackers) ) {	// 如果没有终端返回
						str_html += '<ul>';
						var str_tempData = '';
						
						if ( str_tempFirstTid == '' ) {
							for( var param in obj_trackers ) {
								if ( param ) {
									str_tempData = param;
									break;
								}
							}
							str_tempFirstTid = 'leaf_' + param;	// 第一个分组的第一个定位器 id							
						}
						for ( var param in obj_trackers ) {	// 添加组下面的定位器
							var obj_infoes = obj_trackers[param],
								obj_car = obj_infoes.basic_info,	// 终端基本信息
								obj_trace = obj_infoes.trace_info,	// 甩尾数据
								obj_track = obj_infoes.track_info,	//  开启追踪后的点数据
								arr_alarm = obj_infoes.alarm_info,	// 告警提示列表
								str_tid = param,
								str_oldAlias = obj_car.alias,
								str_alias = dlf.fn_encode(dlf.fn_dealAlias(str_oldAlias)),
								n_degree = obj_car.degree,	// icon_type
								n_iconType = obj_car.icon_type,	// icon_type
								str_mobile = obj_car.mobile,	// 车主手机号
								str_login = obj_car.login,
								n_enClon = obj_car.clongitude,
								n_enClat = obj_car.clatitude,
								n_lon = obj_car.longitude,
								n_lat = obj_car.latitude,
								// n_mannual_status = obj_car.set_mannual_status,	// 退出时默认设防状态 kjj add in 2013.10.09
								obj_currentSelfMarker = obj_selfmarkers[str_tid];
							
							obj_car.trace_info = obj_trace;
							obj_car.track_info = obj_track;
							obj_car.tid = str_tid;
							
							// 1. 判断之前数据是否合法 
							// 2. 新数据是否合法: yes:更新  no: 不更新
							if ( dlf.fn_isEmptyObj(obj_tempCarsData) ) {
								if ( dlf.fn_isEmptyObj(obj_tempCarsData[str_tid]) ) {
									var obj_myCar = obj_tempCarsData[str_tid];
									
									if ( n_lon != 0 && n_lat != 0 && n_enClon != 0 && n_enClat != 0 ) {	// 新数据可用
										obj_carsData[str_tid] = obj_car;
									} else {
										obj_carsData[str_tid] = obj_myCar;
									}
								} else {
									obj_carsData[str_tid] = obj_car;
								}
							} else {
								obj_carsData[str_tid] = obj_car;
							}
							
							// obj_carsData[str_tid] =  obj_car;
							arr_tempTids.push(str_tid); //tid组string 串
							if ( str_login == LOGINOUT ) {
								str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" degree="'+ n_degree +'" icon_type='+ n_iconType +' class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'" alias="'+ str_oldAlias +'">'+ str_alias +'</a></li>';
							} else {
								str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" degree="'+ n_degree +'" icon_type='+ n_iconType +'  class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'" alias="'+ str_oldAlias +'">'+ str_alias +'</a></li>';	
							}
							
							if ( str_tempTid != '' && str_tempTid == str_tid ) {
								b_flg = true;
							}
							/** 
							* 自动完成数据填充:根据旅客姓名和手机号进行搜索
							*/
							var str_tempLabel = str_mobile;
							if ( str_alias != str_mobile ) {
								str_tempLabel = str_oldAlias + ' ' + str_mobile;
							}
							arr_autoCompleteData.push({label: str_tempLabel, value: str_tid});
							// 存储最新的marker信息
							if ( obj_currentSelfMarker ) {
								obj_tempSelfMarker[str_tid] = obj_currentSelfMarker;
								obj_selfmarkers[str_tid] = undefined;
							}
							dlf.fn_checkTrackDatas(str_tid);	// 清除开启追踪后的轨迹线数据
							// 显示告警提示列表
							fn_updateAlarmList(arr_alarm);
							b_isHasTerminal = true;
						}
						str_html += '</ul>';
						// 填充本次数据 为了与下次lastinfo进行比较
						arr_tids[str_groupId] = arr_tempTids;
					} else {
						arr_tids[str_groupId] = [];
					}
					str_html += '</li>';
					arr_groupIds.push(str_groupId);
				}
				str_html += '</ul>';
				// 存储 gids , tids
				obj_newData = {'gids': arr_groupIds, 'tids': arr_tids, 'n_gLen': n_groupLength};
				// 清除被删除的marker
				dlf.fn_createTerminalListClearLayer(obj_selfmarkers);
			}
			obj_selfmarkers = obj_tempSelfMarker;
			if ( !b_isHasTerminal ) {
				obj_carsData = {};
				// 显示告警提示列表
				dlf.fn_closeAlarmPanel();
			}
			$('.j_carList').data('carsData', obj_carsData);	// 存储所有定位器信息
			str_html += '</li></ul>';
			var str_tempNodeId = '';
			/**
			* 设置jstree默认选中的节点
			*/
			if ( str_checkedNodeId == '' || str_checkedNodeId == 'leaf_' || str_checkedNodeId == ' leaf_undefined'  ) {		// 上次没有选中---第一次加载
				if ( str_tempFirstTid != '' ) {	// 拿第一个定位器
					str_tempNodeId = str_tempFirstTid;
				} else {
					str_tempNodeId = str_groupFirstId;
				}
			} else {
				if ( b_flg ) {
					str_tempNodeId = str_checkedNodeId;
				} else {
					str_tempNodeId = str_tempFirstTid == '' ? str_groupFirstId : str_tempFirstTid;
				}
			}
			var b_isDifferentData = fn_lastinfoCompare(obj_newData);
			
			if ( b_isDifferentData ) {	// lastinfo 与当前树节点对比 是否需要重新加载树节点
				/**
				* 判断车辆是否选中
				*/
				var obj_loadTreePanel = $('#corpTree .loadTree');
					
				//当前车辆列表是否数据
				if ( dlf.fn_isEmptyObj(obj_loadTreePanel) ) {
					//如果有车获取车辆选中状态
					dlf.fn_eachCheckedNode('.j_group');
					dlf.fn_eachCheckedNode('.j_leafNode');
				}
				dlf.fn_loadJsTree(str_tempNodeId, str_html);
				dlf.fn_initAutoComplete();
				$('#txtautoComplete').val('请输入定位器名称或号码').addClass('gray');	
			} else {
				// 更新组名和集团名还有 在线离线状态
				fn_updateTreeNode(obj_corp);
			}
			if ( b_isCloseTrackInfowindow ) {
				var obj_carItem = $('.j_carList .j_currentCar'),
					str_tid = obj_carItem.attr('tid');
					
				dlf.fn_switchCar(str_tid, obj_carItem); // 车辆列表切换
			}
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
* kjj 2013-05-21 
* 如果终端有告警，显示告警数据、初始化li的click、mouseover、mouseout事件
* arr_alarm: 告警数据
*/
var obj_trackPoint = {};

function fn_updateAlarmList(arr_alarm) {
	var n_alarmLength = arr_alarm.length,
		obj_table = $('.j_alarmTable'),
		obj_li = $('.j_alarmTable li'),
		arr_temp = obj_table.data('markers'),
		arr_markers = arr_temp == undefined ? [] : arr_temp,
		obj_alarmCon = $('.j_alarm'),
		str_html = '',
		obj_markers = {};
	
	if ( n_alarmLength > 0 ) {
		//str_html+= '<li class="closeAlarm"></li>';
		for ( var x = 0; x < n_alarmLength; x++ ) {
			var obj_alarm = arr_alarm[x],
				str_oldAlias = obj_alarm.alias,
				str_alias = dlf.fn_encode(dlf.fn_dealAlias(str_oldAlias)),
				str_date = dlf.fn_changeNumToDateString(obj_alarm.timestamp),
				n_categroy = obj_alarm.category;
				
			str_html= '<li><label class="colorBlue" title="'+ str_oldAlias +'">'+ str_alias +'</label> 在 '+ str_date +' 发生了 <label class="colorRed">'+ dlf.fn_eventText(n_categroy) +' </label>告警</li>';
			
			if ( obj_li.length > 0 ) {
				obj_li.first().before(str_html);
			} else {
				obj_table.append(str_html);
			}			
			arr_markers.unshift(obj_alarm);	// 存储所有的告警数据
		}
		obj_table.data('markers', arr_markers);
		obj_alarmCon.show();
	}
	
	/** 
	* 初始化奇偶行
	*/
	$('.j_alarmTable li').unbind('mouseover mouseout click').mouseover(function() {
		$(this).css({'background-color': '#FFFACD', 'cursor': 'pointer'});
	}).mouseout(function() {
		$(this).css('background-color', '');
	}).click(function() {
		var obj_this = $(this),
			obj_alarmTable = $('.j_alarmTable'),
			n_num = obj_alarmTable.data('num'),
			arr_markerList = obj_alarmTable.data('markers'),
			n_index = $(this).index(),
			obj_alarm = arr_markerList[n_index],
			n_category = obj_alarm.category,
			n_lng = obj_alarm.clongitude
			n_lat = obj_alarm.clatitude,
			obj_centerPointer = dlf.fn_createMapPoint(n_lng, n_lat),
			obj_marker = null,
			obj_circle = null;
		
		// 清除地图上告警的图层
		dlf.fn_clearAlarmMarker();
		obj_this.addClass('clickedBg').siblings('li').removeClass('clickedBg');	// 添加背景色
		
		if ( n_lng != 0 && n_lat != 0 ) {	// 如果有经纬度则添加marker
			// obj_alarmTable.data('num', n_index);
			obj_marker = dlf.fn_addMarker(obj_alarm, 'alarmInfo', $('.j_currentCar').attr('tid'), true, n_index); // 添加标记
			obj_alarmTable.data('alarmMarker', obj_marker);	// 存储当前的marker 以便下次先删除再添加
			dlf.fn_setOptionsByType('centerAndZoom', obj_centerPointer, 16);
			obj_this.data('marker', obj_marker);
			
			if ( dlf.fn_isBMap() ) {
				obj_marker.setTop(true);
			} else {
				obj_marker.setzIndex(10);
			}
		} else {
			dlf.fn_jNotifyMessage('该告警没有位置信息。', 'message', false, 3000);
			return;
		}
		dlf.fn_drawRegion(n_category, obj_alarm.region_id, obj_centerPointer, 1);	// 画围栏
		/*
		if ( n_category == 7 || n_category == 8 ) {	// 如果是进出围栏告警 画围栏
			var obj_circleData = {},
				n_regionLon = obj_alarm.bounds[1],
				n_regionLat = obj_alarm.bounds[0],
				obj_centerPoint = dlf.fn_createMapPoint(n_regionLon, n_regionLat);
			
			obj_circleData.radius = obj_alarm.region_radius;
			obj_circleData.longitude = n_regionLon;
			obj_circleData.latitude = n_regionLat;
			dlf.fn_setOptionsByType('viewport', [obj_centerPoint, obj_centerPointer]);
			obj_circle = dlf.fn_displayCircle(obj_circleData);	// 调用地图显示圆形
			obj_alarmTable.data('region', obj_circle);
		}*/
		var obj_position = obj_marker.getPosition();
		
		if ( !dlf.fn_isBMap() ) {
			obj_marker.selfInfoWindow.open(mapObj, obj_position);
		} else {
			obj_marker.openInfoWindow(obj_marker.selfInfoWindow);
		}
		mapObj.setCenter(obj_position);
	});
	
}

/**
* kjj 2013-05-24 
* 关闭告警列表 
*/
window.dlf.fn_closeAlarmPanel = function() {
	var obj_alarmPanel = $('.j_alarm'),
		obj_alarmTable = $('.j_alarmTable');

	// 清除告警提示的所有marker和region
	dlf.fn_clearAlarmMarker();
	$('.j_alarmTable').removeData('markers');
	obj_alarmTable.html('');
	obj_alarmPanel.hide();		
}

/**
* kjj 2013-05-22 
* 告警提示marker清除
* n_num: 要清除marker在li上的位置
*/
window.dlf.fn_clearAlarmMarker = function() {
	var obj_alarmTable = $('.j_alarmTable'),
		obj_alarmMarker = obj_alarmTable.data('alarmMarker'),
		obj_alarmRegion = obj_alarmTable.data('region');
	
	if ( obj_alarmMarker ) {
		dlf.fn_clearMapComponent(obj_alarmMarker);
		
		if ( !dlf.fn_isBMap() ) {
			mapObj.clearInfoWindow();
		}
	}
	if ( obj_alarmRegion ) {
		dlf.fn_clearMapComponent(obj_alarmRegion);
	}
}

/**
* 对node节点做遍历查找选中的节点
*/
window.dlf.fn_eachCheckedNode = function(str_eachNode) {
	$(str_eachNode).each(function(leafEvent) { 
		var str_tempLeafClass = $(this).attr('class'), 
			str_tempLeafId = '#' + $(this).attr('id');

		if ( str_tempLeafClass.search(JSTREECLICKED) != -1) {
			arr_treeNodeChecked.push(str_tempLeafId);
		}
	});
}

/**
* 初始化autocomplete
*/
window.dlf.fn_initAutoComplete = function() {
	var obj_compelete = $('#txtautoComplete'),
		str_val = obj_compelete.val();
	
	if ( str_val == '' ) {
		str_val = '请输入定位器名称';
	}
	// autocomplete	自动完成 初始化
	obj_compelete.keyup(function(event) {
		if ( event.keyCode === $.ui.keyCode.TAB && $(this).data('autocomplete').menu.active ) {
			event.preventDefault();
		}
		$(this).autocomplete('search');
	}).autocomplete({
		source: arr_autoCompleteData,
		select: function(event, ui) {
			var str_tid = ui.item.value,
				obj_itemLi = $('.j_carList a[tid='+ str_tid +']'),
				str_crntTid = $('.j_leafNode a[class*='+ JSTREECLICKED +']').attr('tid');

			$('#txtautoComplete').val( ui.item.label);
			if ( str_crntTid == str_tid ) {
				return false;
			}
			dlf.fn_switchCar(str_tid, obj_itemLi);
			return false;
		}
	});
}

/**
* 更新树节点的数据
* obj_corp: 最新的集团数据
*/
function fn_updateTreeNode(obj_corp) {
	var arr_groups = obj_corp.groups,	// all groups 
		n_groupLength = arr_groups.length,	// group length
		str_corpName = obj_corp.name,	// corp name
		str_tempCorpName = str_corpName.length > 10 ? str_corpName.substr(0,10)+ '...' : str_corpName,
		str_corpId = obj_corp.cid;		// corp id
	
	$('.j_corp a[corpId='+ str_corpId +']').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempCorpName).attr('title', str_corpName);	// 更新集团名 <img src="/static/images/corpImages/corp.png">
	for ( var gIndex in arr_groups ) {
		var obj_group = arr_groups[gIndex],
			str_groupName = obj_group.name,
			n_groupNameLng = str_groupName.length,
			str_tempGroupName = dlf.fn_dealAlias(str_groupName), // n_groupNameLng>10 ? str_groupName.substr(0,10)+ '...' : str_groupName,
			obj_trackers = obj_group.trackers;	// 所有终端 arr_cars

		$('#group_'+ obj_group.gid).html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempGroupName).attr('title', str_groupName);	// 更新组名
		
		if ( dlf.fn_isEmptyObj(obj_trackers) ) {
			for ( var param in obj_trackers ) {
			
				var obj_infoes = obj_trackers[param],
					obj_car = obj_infoes.basic_info,	// 终端基本信息
					obj_trace = obj_infoes.trace_info,	// 甩尾点数据
					obj_track = obj_infoes.track_info,	// 开启追踪点数据
					str_tid = param,
					n_login = obj_car.login,
					str_tmobile = obj_car.mobile,
					str_alias = obj_car.alias,
					n_iconType = obj_car.icon_type,	
					str_tempAlias = dlf.fn_encode(dlf.fn_dealAlias(str_alias)),
					obj_leaf = $('#leaf_' + str_tid),
					str_imgUrl = '',
					n_lon = obj_car.longitude,
					n_lat = obj_car.latitude,
					n_clon = obj_car.clongitude/NUMLNGLAT,	
					n_clat = obj_car.clatitude/NUMLNGLAT;
				
				obj_car.tid = str_tid;
				if ( n_login == LOGINOUT ) {
					str_imgUrl = 'offline.png';
				} else {
					str_imgUrl = 'online.png';
				}
				obj_leaf.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias).attr('title', str_tmobile).attr('clogin', n_login).attr('alias', str_alias).attr('icon_type', n_iconType);	
				
				if ( str_currentTid == str_tid  ) {
					if ( n_clon != 0 && n_clat != 0 ) {
						dlf.fn_updateTerminalInfo(obj_car);
					}					
				}
				if ( n_lon != 0 && n_lat != 0 ) {
					if ( n_clon != 0 && n_clat != 0 ) {
						obj_car.trace_info = obj_trace;
						obj_car.track_info = obj_track;
						dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
						if ( dlf.fn_isEmptyObj(obj_trace) ) {	// 生成甩尾数据
							obj_trace.tid = str_tid;
						}
					} else {
						dlf.fn_translateToBMapPoint(n_lon, n_lat, 'lastposition', obj_car);	// 前台偏转 kjj 2013-09-27
					}
				}
			}
		}
	}
	fn_updateAllTerminalLogin();
	dlf.fn_setCorpIconDiffBrowser();
}

window.dlf.fn_setCorpIconDiffBrowser = function () {
	/*if ( $.browser.msie && ($.browser.version == "7.0") ) {
		$('.corpNode ins').css('backgroundPosition', '0px 0px');
	} else {
		$('.corpNode ins').css('backgroundPosition', '0px');
	}*/
	$('.corpNode ins[class=jstree-icon]').css('backgroundPosition', '0px 0px');
}

/**
* 更新车辆状态
*/
function fn_updateAllTerminalLogin() {
	$('.j_terminal').each(function() {
		dlf.fn_updateTerminalLogin($(this));
	});
}

/**
* 设置定位器的图标
* n_iconType: 图标类型
* n_login:  在线状态
*/
function fn_setIconType(n_iconType, n_login) {
	var str_tempImgUrl = '';
	
	if ( n_iconType == 0 ) {	// 车或摩托车
		str_tempImgUrl = 'icon_car';
	} else if ( n_iconType == 1  ) {
		str_tempImgUrl = 'icon_moto';
	} else if ( n_iconType == 2 ) {	// 人
		str_tempImgUrl = 'icon_person';
	} else if ( n_iconType == 3 ) {
		str_tempImgUrl = 'icon_default';
	}
	return str_tempImgUrl + n_login + '.png';
}

/**
* obj_this: 要更新的定位器对象
* 更新定位器在线离线图标
*/
window.dlf.fn_updateTerminalLogin = function(obj_this) {
	var	str_login = obj_this.attr('clogin'),
		n_iconType = obj_this.attr('icon_type'),	// icon_type
		str_imgUrl = '',
		str_color = '',
		obj_ins = obj_this.children('ins[class=jstree-icon]');	// todo
	
	if ( str_login == LOGINOUT ) {
		// str_imgUrl = 'offline.png';
		str_color = 'gray';
	} else {
		// str_imgUrl = 'online.png';
		str_color = '#24d317';
	}
	str_imgUrl = fn_setIconType(n_iconType, str_login);	// 设置图标url
	obj_this.css('color', str_color);
	obj_ins.css('background', 'url("/static/images/corpImages/terminalIcons/'+ str_imgUrl +'") no-repeat');
	if ( $.browser.msie ) {
		if ( $.browser.version == "7.0" ) {
			obj_ins.css('backgroundPosition', '0px -1px');
		} else if ( $.browser.version == "6.0"  ) {
			obj_ins.css('backgroundPosition', '0px 25px');
		} else {
			obj_ins.css('backgroundPosition', '0px 2px');
		}
	} else {
		obj_ins.css('backgroundPosition', '0px 2px');
	}
}

/**
* 集团用户 /terminal get和put的时候更新最新的定位器别名
* cnum: 要更新的定位器别名
* str_tid: 集团用户右键参数设置中修改定位器名称
*/
window.dlf.fn_updateCorpCnum = function(cnum) {
	var obj_current = $('.j_currentCar'),
		str_cnum = cnum['corp_cnum'] == undefined ? cnum : cnum['corp_cnum'],
		str_tmobile = obj_current.attr('title'),
		str_tempAlias = str_cnum,
		str_tid = str_currentTid,
		obj_selfMarker = obj_selfmarkers[str_tid],
		b_mapType = dlf.fn_isBMap();
	
	if ( str_cnum == '' ) {
		str_tempAlias = str_tmobile;
	}
	str_tempAlias = dlf.fn_encode(dlf.fn_dealAlias(str_tempAlias));
	obj_current.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias);
	dlf.fn_updateTerminalLogin(obj_current);
	for ( var index in arr_autoCompleteData ) {
		var obj_terminal = arr_autoCompleteData[index],
			str_newLabel = '',
			str_tempTid = obj_terminal.value,	// tid
			str_label = obj_terminal.label;	// alias 或 tmobile
		// 当前终端的、alias不是tmobile
		if ( str_tempTid == str_tid ) {
			if ( str_cnum == '' || str_cnum ==  str_tmobile ) {
				str_newLabel = str_tmobile;
			} else {
				str_newLabel = str_cnum + ' ' + str_tmobile;
			}
			obj_terminal.label = str_newLabel;
			dlf.fn_initAutoComplete();
			// todo 修改marker上的定位器名称和label的定位器名称
		}
	}
	if ( obj_selfMarker ) {	// 修改 marker label 别名
		var	str_content = obj_selfMarker.selfInfoWindow.getContent(),
			n_beginNum = str_content.indexOf('定位器：')+4,
			n_endNum = str_content.indexOf('</h4>'),
			str_oldname = str_content.substring(n_beginNum, n_endNum),
			str_content = str_content.replace(str_oldname, str_tempAlias);
		
		if ( b_mapType ) {	// 百度地图修改label
			var obj_selfLabel = obj_selfMarker.selfLable;
		
			obj_selfLabel.setContent(str_tempAlias);	// label上的alias值
			obj_selfMarker.setLabel(obj_selfLabel);	// 设置label  obj_carA.data('selfLable')
		}
		obj_selfmarkers[str_tid].selfInfoWindow.setContent(str_content);
		$('#markerWindowtitle h4[tid='+ str_tid +']').html('定位器：' + str_tempAlias);
		dlf.fn_updateOpenTrackStatusColor(str_tid);
	}
}

/**
* 对比两次lastinfo的数据是否一致，不一致重新加载树
* obj_newData: 最新的lastinfo数据
*/
function fn_lastinfoCompare(obj_newData) {
	var n_newDataLen = obj_newData.n_gLen,		// new lastinfo 的group数量
		obj_groups = $('.j_group'),
		n_oldDataLen = 0, 	// 所有分组数量
		arr_newGids = obj_newData.gids,	// 所有新分组
		arr_newTids = obj_newData.tids;	// 所有新tids
		
	if ( !obj_groups ) {
		return true;
	} else {
		n_oldDataLen = obj_groups.length
	}
	if ( n_newDataLen != n_oldDataLen ) {	// 分组数不同重新加载
		return true;
	}
	// valid gids
	for ( var gid in arr_newGids ) {
		var str_gid = arr_newGids[gid];
		
		if ( str_gid != '' ) {
			if ( $('#group_' + str_gid ).length <= 0 ) {	// 树节点上没有新的组
				return true;
			}
		}
	}
	// valid tids
	for ( var gid in arr_newTids ) {
		var arr_newStrTids = arr_newTids[gid],
			n_newTidLength = arr_newStrTids.length,
			n_treeLength = $('#group_'+  gid).siblings('ul').find('.j_terminal').length;
		
		if ( n_newTidLength != n_treeLength ) {
			return true;
		}
		for ( var tid in arr_newStrTids ) {
			var str_tid = arr_newStrTids[tid];
			
			if ( str_tid != '' ) {
				if ( $('#leaf_' + str_tid ).length <= 0 ) {
					str_currentTid = '';
					return true;
				}
			}
		}
	}
	return false;
}

/**
* 新建组
* cid: 集团id
* str_newName: 组名
* obj_rollBack: 如果新建失败要回滚的对象
* obj_newNode: 新增的组节点
*/
function fn_createGroup(cid, str_newName, obj_rollBack, obj_newNode) {
	if ( str_newName == '' ) {
		dlf.fn_jNotifyMessage('分组名称不能为空。', 'message', false, 3000);
		$.jstree.rollback(obj_rollBack);
		return false;
	} else {
		if ( !fn_checkGroupName(str_newName, obj_rollBack) ) {
			var obj_param = {'name': str_newName, 'cid': cid};
			
			$.post_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
				if ( data.status == 0 ) {
					var n_gid = data.gid;
					obj_newNode.addClass('j_group').children('a').attr('groupId', n_gid).addClass('groupNode').attr('id', 'group_' + n_gid).css('color', '#000000');
					dlf.fn_corpGetCarData();	// 重新加载树 2013.09.04
					$('#corpTree').jstree('refresh',-1);
				} else {
					$.jstree.rollback(obj_rollBack);
				}
			});
		}
	}
}

/**
* 判断组名是否重复
*/
function fn_checkGroupName(str_name, node, str_gid) {
	var b_flg = false,
		n_length = str_name.length;
	
	if ( n_length > 0 ) {
		// 验证集团名称合法性
		if ( n_length > 20 ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('分组名称最大长度是20个汉字或字符！', 'message', false, 3000);
			b_flg = true;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_name) ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('分组名称只能由数字、英文、中文组成！', 'message', false, 3000); // 查询状态不正确,错误提示
			b_flg = true;
		}
	} else {
		$.jstree.rollback(node);
		dlf.fn_jNotifyMessage('分组名称不能为空！', 'message', false, 3000);
		b_flg = true;
	}
	
	$('.groupNode[groupid != ' + str_gid+ ']').each(function() {
		if ( $.trim($(this).text()) == str_name  ) {
			if ( node ) {
				$.jstree.rollback(node);
			}
			dlf.fn_jNotifyMessage('该分组已存在。', 'message', false, 3000);
			b_flg = true;
		}
	});
	return b_flg;
}

/**
* 重命名组
*/
function fn_renameGroup(gid, str_name, node) {
	var obj_param = {'name': str_name, 'gid': gid};
	if ( !fn_checkGroupName(str_name, node, gid) ) {
		$.put_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
			if ( data.status == 0 ) {	
				dlf.fn_corpGetCarData();	// 重新加载树2013.09.04
				$('#corpTree').jstree('refresh',-1);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
			}
		});
	}
}

/**
* 删除组
*/
function fn_removeGroup(node) {
	var str_param = node.children('a').attr('groupid');
	
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	if ( confirm('确定要删除该分组吗？') ) {
		$.delete_(GROUPS_URL + '?ids=' + str_param, '', function (data) {
			if ( data.status == 0 ) {
				$("#corpTree").jstree('remove');
				dlf.fn_corpGetCarData();	// 重新加载树2013.09.04
				$('#corpTree').jstree('refresh',-1);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
			}
		});
	}
}

/**
* 拖拽组、移动至其他组
*/
function fn_moveGroup(arr_tids, n_newGroupId, obj_rlbk, node_id) {
	var obj_param = {'tids': arr_tids, 'gid': n_newGroupId}

	if ( node_id ) {
		$('#corpTree').jstree('move_node', '#' + node_id, '#groupNode_' + n_newGroupId);
	} else {
		$.post_(GROUPTRANSFER_URL, JSON.stringify(obj_param), function (data) {
			if ( data.status == 0 ) {
				dlf.fn_corpGetCarData(true);	// 重新加载树2013.09.04
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 执行操作失败，提示错误消息
				$.jstree.rollback(obj_rlbk);
			}
		});
	}
}

/**
* 重命名集团名称 
*/
function fn_renameCorp(cid, str_name, node) {
	var obj_param = {'name': str_name, 'cid': cid},
		n_length = str_name.length;
	
	// 验证集团名称合法性
	if ( n_length > 0 ) {
		if ( n_length > 20 ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('集团名称最多可输入20个汉字或字符！', 'message', false, 3000); // 查询状态不正确,错误提示
			return;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_name) ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('集团名称只能由中文、英文、数字组成组成！', 'message', false, 3000); // 查询状态不正确,错误提示
			return;
		}
	} else {
		$.jstree.rollback(node);
		dlf.fn_jNotifyMessage('集团名称不能为空！', 'message', false, 3000); // 查询状态不正确,错误提示
		return;
	}
	
	$.put_(CORP_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			$.jstree.rollback(node);
		} else {
			var str_tempCName = str_name.length > 10 ? str_name.substr(0,10)+ '...' : str_name;
			$('.corpNode').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempCName).attr('title', str_name).children().eq(1).css('background', 'url("/static/images/corpImages/corp.png") 0px no-repeat');;
		}
	});
}

/**
* 添加单个定位器
*/
function fn_initCreateTerminal(obj_node, str_groupId) {
	$('.cTerminalList input[type=text]').val();
	$('#c_icon_type0').attr('checked', true);
	dlf.fn_dialogPosition('cTerminal'); // 新增定位器dialog显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化报警查询选择时间
	*/
	$('#hidGroupId').val(str_groupId);	// 保存groupId
	$('.j_corpData').val('');
	$('#hidTMobile').val('');
}

/**
* 保存单个定位器
*/
window.dlf.fn_cTerminalSave = function() {
	var str_tmobile = $('#c_tmobile').val(),
		str_umobile = $('#c_umobile').val(),
		str_cnum = $('#c_cnum').val(),
		n_iconType = parseInt($('.cTerminalList input:checked').val());
		n_groupId = parseInt($('#hidGroupId').val()),
		obj_corpData = {};
		
	obj_corpData['tmobile'] = str_tmobile;
	obj_corpData['group_id'] = n_groupId;
	obj_corpData['umobile'] = str_umobile;
	obj_corpData['cnum'] = str_cnum;
	obj_corpData['icon_type'] = n_iconType;
	dlf.fn_jsonPost(TERMINALCORP_URL, obj_corpData, 'cTerminal', '定位器信息保存中');
}

/**
* 获取下一年的时间
*/
function fn_getNextYear(str_nowDate) {
	var date = new Date(str_nowDate);
	date.setYear(date.getFullYear()+1);
	return date.getTime();
}

/**
* 删除定位器
*/
function fn_removeTerminal(node) {
	var obj_target = node.children('a'),
		str_login = obj_target.attr('clogin'),
		str_param = obj_target.attr('tid'),
		obj_clearDataWp = $('#clearDataWrapper'), 
		obj_ck = $('#clearDataCk');
		
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	
	obj_clearDataWp.css({'left': '40%'}).show();
	obj_ck.removeAttr('checked');
	$('#clearDataMsgCon').html('确定要删除该定位器吗？');
	dlf.fn_lockScreen(); // 添加页面遮罩
	
	
	$('#clearDataSure').unbind('click').click(function(e) {
		obj_clearDataWp.hide();
		var n_clearFlag = obj_ck.attr('checked') ? 1 : 0,
			str_delTerminalUrl = TERMINALCORP_URL+'?tid='+ str_param +'&flag='+ n_clearFlag;
			
		dlf.fn_jNotifyMessage('定位器正在删除中' + WAITIMG, 'message', true);
		$.delete_(str_delTerminalUrl, '', function (data) {
			if ( data.status == 0 ) {
				fn_updateTerminalCount('sub', 1);				
				$("#corpTree").jstree('remove');				
				// 删除地图marker
				obj_actionTrack[str_param].status = '';
				if ( obj_selfmarkers[str_param] ) {
					mapObj.removeOverlay(obj_selfmarkers[str_param]);
					delete obj_selfmarkers[str_param];
					delete obj_carsData[str_param];
					dlf.fn_checkTrackDatas(str_param, true);	// 删除开启追踪的轨迹线
				}
				var obj_current = $('.' + JSTREECLICKED),
					b_class = obj_current.hasClass('groupNode'),
					str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
				
				if ( str_tid != undefined ) {
					obj_current = $('.j_terminal').eq(0);
					$('.' + JSTREECLICKED).removeClass(JSTREECLICKED);
					obj_current.addClass(JSTREECLICKED);
					dlf.fn_switchCar(str_tid, obj_current);
				} else {
					dlf.fn_initCarInfo();
				}
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			}
			dlf.fn_unLockScreen(); // 去除页面遮罩
		});
	});
	$('#clearDataCancel').unbind('click').click(function(e) {
		obj_clearDataWp.hide();
		dlf.fn_unLockScreen(); // 去除页面遮罩
	});
}

/**
* 批量删除数据回显
*/
function fn_initBatchDeleteData(obj_params) {
	var obj_param = {'tids': obj_params.tids, 'flag': 0},
		obj_clearDataWp = $('#clearDataWrapper'), 
		obj_maskLayer = $('#maskLayer'), 
		obj_ck = $('#clearDataCk');
	
	dlf.fn_echoData('batchDeleteTable', obj_params, '删除');
	$('.j_batchDeleteHead').html(obj_params.gname);	// 表头显示组名
		
	$('.j_batchDelete').unbind('click').bind('click', function() {
		dlf.fn_lockScreen(); // 添加页面遮罩
		obj_clearDataWp.css({'left': '40%'}).show();
		obj_ck.removeAttr('checked');
		$('#clearDataMsgCon').html('确定要删除以上定位器吗？');
		obj_maskLayer.css('z-index', 1002);
		
		$('#clearDataSure').unbind('click').click(function(e) {
			obj_clearDataWp.hide();
			obj_param.flag = obj_ck.attr('checked') ? 1 : 0;
			
			dlf.fn_jNotifyMessage('定位器正在删除中' + WAITIMG, 'message', true);
			
			$.post_(BATCHDELETE_URL, JSON.stringify(obj_param), function (data) {
				var arr_res = data.res,	
					arr_success = [],
					n_successLen = 0;
				
				if ( data.status == 0 ) {
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					// 返回数据res中提取删除成功的终端
					for ( var i in arr_res ) {
						var obj_result = arr_res[i],
							n_success = obj_result.status,
							str_tid = obj_result.tid,
							str_status = '',
							obj_updateTd = $('.batchDeleteTable tr td[tid='+ str_tid +']');
							
						if ( n_success == 0 ) {
							arr_success.push(str_tid);
							str_status = '删除成功';
							obj_updateTd.addClass('fileStatus4');
						} else if ( n_success == -1 ) {
							str_status = '删除失败';
							obj_updateTd.addClass('fileStatus3');
						}
						obj_updateTd.html(str_status);	// 更新保存状态
					}
					n_successLen = arr_success.length;	// 成功删除的终端个数
					fn_updateTerminalCount('sub', n_successLen);
					$('.j_batchDelete').attr('disabled', true);	// 批量删除按钮变成灰色并且不可用
					/**
					* 删除节点
					*/
					for ( var i in arr_success ) {
						var str_tid = arr_success[i];
						
						$("#corpTree").jstree('remove', '#leafNode_' + str_tid );
					}
					//$("#corpTree").jstree('remove');				
					// 删除地图marker
					for ( var i = 0; i < n_successLen; i++ ) {
						var str_tid = arr_success[i];
						
						if ( obj_selfmarkers[str_tid] ) {
							mapObj.removeOverlay(obj_selfmarkers[str_tid]);
							delete obj_selfmarkers[str_tid];
						}
					}
					var obj_current = $('.'+ JSTREECLICKED),
						b_class = obj_current.hasClass('groupNode'),
						str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
							
					if ( str_tid != undefined ) {
						if ( b_class ) {
							obj_current = $('.j_terminal').eq(0);
						}
						$('.'+ JSTREECLICKED ).removeClass(JSTREECLICKED);
						obj_current.addClass(JSTREECLICKED);
						dlf.fn_switchCar(str_tid, obj_current);
					} else {
						dlf.fn_initCarInfo();
					}
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				} 
				dlf.fn_unLockScreen(); // 添加页面遮罩
				obj_maskLayer.css('z-index', 1000);
			});
		});
		$('#clearDataCancel').unbind('click').click(function(e) {
			obj_clearDataWp.hide();
			dlf.fn_unLockScreen(); // 去除页面遮罩
			obj_maskLayer.css('z-index', 1000);
		});
	});
	
}

/**
* 批量删除定位器
*/
function fn_batchRemoveTerminals(obj_params) {
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	dlf.fn_dialogPosition('batchDelete');	// 设置dialog的位置
	// 数据回显
	$('.j_batchDelete').attr('disabled', false);	// 批量删除按钮变成绿色并且可用
	fn_initBatchDeleteData(obj_params);
}

/**
*二级菜单事件
*/
window.dlf.fn_fillNavItem = function() {
	var obj_navItemUl = $('.j_countNavItem'),
		b_status = obj_navItemUl.is(':visible'),
		obj_navOffset = $('#recordCount').offset();
	
	obj_navItemUl.css('left',obj_navOffset.left - 5).show(); // 二级单显示
	/*二级菜单的滑过样式*/
	$('.j_countNavItem li a').unbind('mousedown mouseover mouseout').mouseout(function(event) {
		// $(this).removeClass('countUlItemHover');
		obj_navItemUl.hide();
		$('.j_countRecord').bind('mouseover', function() {
			dlf.fn_fillNavItem();
		});
	}).mouseover(function(event) {
		// $(this).addClass('countUlItemHover');
		obj_navItemUl.show();
		$('.j_countRecord').unbind('mouseover');
	});
}

/**
* 判断二级菜单是否显示,如果显示进行隐藏
*/
window.dlf.fn_secondNavValid = function() { 
	var obj_navItem = $('.j_countNavItem'), 
		f_hidden = obj_navItem.is(':hidden');
	
	if ( !f_hidden ) {
		obj_navItem.hide();
	}
}

/**
* 验证定位器手机号
*/
window.dlf.fn_checkTMobile = function(str_tmobile) {
	$.get_(CHECKMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			$('#hidTMobile').val('1');
			dlf.fn_jNotifyMessage('定位器手机号已存在。', 'message', false, 5000);
			return;
		} else {
			$('#hidTMobile').val('');
		}
	});
}

/**
* 操作员手机号已存在。
*/
window.dlf.fn_checkOperatorMobile = function(str_tmobile) {
	$.get_(CHECKOPERATORMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			var str_msg = data.message;
			
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
			$('#hidOperatorMobile').val(str_msg);
			return;
		} else {
			$('#hidOperatorMobile').val('');
		}
	});
}
/**
* 验证乘客手机号
*/
window.dlf.fn_checkPassengerMobile = function(str_tmobile) {
	$.get_(CHECKPASSENGERMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage('乘客手机号已存在。', 'message', false, 5000);
			$('#hidPassengerMobile').val('1');
			return;
		} else {
			$('#hidPassengerMobile').val('');
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

/**
* 批量导入文件
*/
function fn_initBatchImport(gid, gname) {
	$('.fileInfoTable').html('');
	var obj_upfile = window.frames['fileUploadIframe'].document.getElementById('fileUploadTable'),
		obj_msg = window.frames['fileUploadIframe'].document.getElementById('jNotifyMessage');
		
	$(obj_upfile).remove().html('');
	$(obj_msg).html('');
	dlf.fn_dialogPosition('fileUpload');	// 设置dialog的位置
	$('#hidGid').val(gid);
	$('#hidGName').val(gname);
	$('#fileUploadIframe').attr('src', BATCHIMPORT_URL);
}

/**
* 数据回显：批量删除定位器、批量设防撤防
*/
window.dlf.fn_echoData = function(str_tableName, obj_params, str_msg) {
	var arr_dataes = obj_params.characters;
		obj_table = $('.' + str_tableName + ' tbody'),
		obj_head = $('.' + str_tableName + ' thead th');
	
	obj_table.html('');	// 清空表格数据
	for ( var i = 0; i < arr_dataes.length; i++ ) {
		var obj = arr_dataes[i],
			str_defendMsg = obj.mennual_status == 1 ? '已设防' : '未设防',
			str_html = '';
		
		str_html = '<tr><td>'+ obj.alias +'</td><td>'+ obj.tmobile +'</td>';
		if ( str_msg != '删除' ) {	// 设防或撤防
			str_html += '<td>'+ str_defendMsg +'</td>';
		}
		str_html += '<td tid='+ obj.tid +' class="fileStatus1">等待'+ str_msg +'</td>'
		str_html += '</tr>';
		obj_table.append(str_html);	// 填充要删除的数据
	}
	obj_head.html(obj_params.gname);	// 表头显示组名
}
})();