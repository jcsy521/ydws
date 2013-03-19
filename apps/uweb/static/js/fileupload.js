/*
 * Style File - jQuery plugin for styling file input elements
 *  
 * Copyright (c) 2007-2008 Mika Tuupola
 *
 * Licensed under the MIT license:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * Based on work by Shaun Inman
 *   http://www.shauninman.com/archive/2007/09/10/styling_file_inputs_with_css_and_the_dom
 *
 * Revision: $Id: jquery.filestyle.js 303 2008-01-30 13:53:24Z tuupola $
 *
 */

(function($) {
    
    $.fn.filestyle = function(options) {
                
        /* TODO: This should not override CSS. */
        var settings = {
            width : 250
        };
                
        if(options) {
            $.extend(settings, options);
        };
                        
        return this.each(function() {
            
            var self = this;
            var wrapper = $("<div>")
                            .css({
                                "width": (settings.imagewidth + 200) + "px",
                                "height": settings.imageheight + "px",
                                "background": "url(" + settings.image + ") 0 0 no-repeat #EEEEEE",
                                "background-position": "left",
                                "display": "block",
                                "position": "absolute",
                                "overflow": "hidden"
                            });
                            
            var filename = $('<input class="file">')
                             .addClass($(self).attr("class"))
                             .css({
                                 "display": "inline",
                                 "width": settings.width + "px"
                             });

            $(self).before(filename);
            $(self).wrap(wrapper);

            $(self).css({
                        "position": "relative",
                        "height": settings.imageheight + "px",
                        "width": ( settings.width ) + "px",
                        "display": "inline",
                        "cursor": "pointer",
                        "opacity": "0.0"
                    });

            if ($.browser.mozilla) {
                if (/Win/.test(navigator.platform)) {
                    $(self).css("margin-left", "-81px");                    
                } else {
                    $(self).css("margin-left", "-168px");                    
                };
            } else {
                $(self).css("margin-left", settings.imagewidth - settings.width + "px");                
            };

            $(self).bind("change", function() {
				var obj_this = $(self),
					obj_msg = $('.j_uploadError'),
					obj_resultTab = $('.fileInfoTable'),
					str_val = obj_this.val();
				
				obj_msg.html('');
				var str  = str_val.substr(str_val.lastIndexOf('.') + 1, str_val.length);
				// 上传文件后判断后缀名
				if ( str != 'xlsx' && str != 'xls' ) {
					obj_msg.html('上传文件格式错误，请重新上传。');
					obj_this.val('');
				} else {
					str_result = '<tr><td>'+ str_val +'</td><td><input type="submit" class="operationBtn j_startUpload" value="开始上传"  /></td></tr>';
					obj_resultTab.html(str_result);
				}
				
				// 取消上传文件
				/*$('.j_delete').unbind('click').bind('click', function() {
					var obj_currentTr = $(this).parent().parent();
					
					obj_currentTr.remove();
				});*/
                filename.val($(self).val());
				
            });
        });
	};
	
})(jQuery);