(function($){
/*
 * JQuery Plugin for Entry Edits
 *
*/
    $.extend($.fn, {
        swapClass: function(c1, c2) {
            return this.each(function() {
                var $this = $(this);
                if ( $.className.has(this, c1) )
                    $this.removeClass(c1).addClass(c2);
                else if ( $.className.has(this, c2) )
                    $this.removeClass(c2).addClass(c1);
            });
        }
    });
    
    /*
     * Generic Default static add UI message
     */
    $.extend($, {
         showmessage: function(msg) {
             $("#hiddenmessage").show();
             //$("#hiddenmessage div:nth-child(2)").html(msg);
             $("#hiddenmessage").html(msg);
             //$("#hiddenmessage").animate({height: 'toggle',opacity: 'toggle'},{duration: 4000});
         }
    });
    //If the ds scope not available, add it
    $.ds = $.ds || {};

    /*
    *   Blog Web Admin
    */
    $.fn.blogadmin = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-blogadmin")) new $.ds.blogadmin(this, o);
        });
    }
    $.ds.blogadmin = function(el, o) {
        var options = {
            permalink_sel: '#real_permalink',
            permalink_span: '#editable-post-name',
            permalink_edit: '#editable-post-href',
            permalink_div: '#permalink_div',
            title: '#title'
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $.data(this.element, "ds-blogadmin", this);
        $(options.title).blur(function(e){
            self.show(this);
        });
        //"#editable-post-name,#editable-post-href"
        $(options.permalink_span + ',' + options.permalink_edit).click(function() {
            self.slugedit(this);
         });
         $('#form_cancel').click(function() {
             //this
          });
    }
    $.extend($.ds.blogadmin.prototype, {
        slugblur: function (el) {
            var self = this;
            $(self.options.permalink_sel).hide();
            $(self.options.permalink_span).html($(self.options.permalink_sel).val());
        },
        show: function (el) {
            var self = this;
            $(self.options.permalink_div).show();
            $(self.options.permalink_sel).hide();
            $(self.options.permalink_span).html($(self.options.permalink_sel).val());
            var slug = $(self.options.permalink_sel).val();
            if (slug == '') {
                slug = $(self.options.title).val().replace(/ /g,'-').toLowerCase().replace(/[^a-z\-]/g,'');
                $(self.options.permalink_sel).val(slug);
            }else{
                
            }
            $(self.options.permalink_span).html(slug);
            
            $.showmessage('inside show' + self.options.permalink_sel);
        },
        slugedit: function (el) {
            var self = this;
            self.show();
            $.showmessage('inside slugedit');
            $(self.options.permalink_sel).show().focus();
            $(self.options.permalink_sel).keypress(function(e){
                $.showmessage('inside keypress');
                var key = e.charCode ? e.charCode : e.keyCode ? e.keyCode : 0;
                // Make sure not to save entire form, just slug if the hit return
                if ((13 == key) || (27 == key)) {
                    self.slugblur();
                    return false;
                }
            });
            $(self.options.permalink_sel).blur(function(e){
                $.showmessage('blur from inside of focus');
                $(this).hide();
                $(self.options.permalink_span).html($(this).val());
                //self.slugblur();
            });
        }
    });
})(jQuery);