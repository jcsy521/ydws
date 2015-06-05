/*
* test
*/
(function () {
	$('#searchUrl, #searchMethod,#searchArgument').val('');
	
	$('#searchBtn').unbind('click').click(function(e) {


		var str_url = $.trim($('#searchUrl').val()),
			str_method = $.trim($('#searchMethod').val()).toUpperCase(),
			str_argument = $.trim($('#searchArgument').val()),
			arr_argument = [],
			obj_search = {};
		
		if ( str_url == '' ) {alert('能好好玩耍不?');return;}
		if ( str_method == '' ) {alert('能好好交流不?');return;}
		if ( str_argument == '' ) {alert('能好好说不?');return;}
		
		arr_argument = str_argument.split(',');
		
		if ( arr_argument.length <= 0 ) {alert('没法玩了.');return;}
		
		for( var param in arr_argument ) {
			var arr_argument2 = arr_argument[param].split(':');
			
			obj_search[arr_argument2[0]] = arr_argument2[1];
		}
		console.log('log1:   ', '     url:', str_url, '   meghtod:' ,str_method,'    要发送的东西:  ',obj_search);
		
		$.ajax({ 
			url: str_url, 
			type: str_method,
			dataType: 'json', 
			data: JSON.stringify(obj_search),
			
			complete: function(XMLHttpRequest, textStatus){
				console.log("[openapi] complete", XMLHttpRequest, textStatus);
			},
		

			success: function(data){
				console.log("[openapi] success: ", data);
				$('#resDatas').append('status: '+data.status+', message: '+data.message+',sign:'+data.sign+',token:'+data.token+',res:'+data.res);
				$('#resDatas').append('<hr>');
			}
		});
		
	});
})();