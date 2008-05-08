(function($){
/*
 * Demisauce Core admin Javascript:  these are core internal javascript
 * components used only for DS admin server.  The client pieces that
 * would go on apps that utilize services are in the ds.client.{plugin}.js
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
             $("#hiddenmessage div:nth-child(2)").html(msg);
             $("#hiddenmessage").animate({height: 'toggle',opacity: 'toggle'},{duration: 4000});
         }
    });
    //If the Demisauce scope is not availalable, add it
    $.ds = $.ds || {};
    
    /*
    *  Demisauce CMS Email Web Admin
    */
    $.fn.emailadmin = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-emailadmin")) new $.ds.emailadmin(this, o);
        });
    }
    $.ds.emailadmin = function(el, o) {
        var options = {
            currentfolder: null,
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $('a.cmsedit').click(function(){
            self.edit(this);
        });
        $.data(this.element, "ds-emailadmin", this);
    }
    $.extend($.ds.emailadmin.prototype, {
        edit: function (el) {
            var id = $(el).attr('objid');
            alert(' in email edit');
            if (id > 0) {
                $.get("/email/edit/" + id, function(data){
                    $("#EmailItemFormWrapper").html(data);
                });
            }
        }
    });
    /*
    *  Demisauce CMS Admin page plugin
    */
    $.fn.cmsadmin = function(o) {
        return this.each(function() {
            if (!$(this).is(".ds-cmsadmin")) new $.ds.cmsadmin(this, o);
        });
    }
    $.ds.cmsadmin = function(el, o) {
        var options = {
            currentfolder: null,
        };
        o = o || {}; $.extend(options, o); //Extend and copy options
        this.element = el; var self = this; //Do bindings
        self.options = options;
        $.data(this.element, "ds-cmsadmin", this);
        //$('a.folderlink').treenode({fake:'not'});
        $('a.folderlink,a.folder.empty').click(function(){
            $('.activefolder').removeClass('activefolder');
            $(this).parent().addClass('activefolder');
            self.folderview(this);
        });
        $('span.file').click(function(){
            self.edit(this);
        });
    }
    $.extend($.ds.cmsadmin.prototype, {
        edit: function (el) {
            var self = this;
            var id = $(el).attr('objid');
            $('.activefolder').removeClass('activefolder');
            $(el).addClass('activefolder');
            $.get("/cms/edit/" + id, function(data){
                $("#CmsItemFormWrapper").html(data);
                self.formsetup();
            });
        },
        formsetup: function () {
            $('#cmsform').submit(function() {
                var item_type = $('#item_type').val();
                var title = $('#title').val();
                var id = $('#objectid').val();
                var parentid = $('#parentid').val();
                var newid = 0;
                $(this).ajaxSubmit({success: function(responseText, statusText)  {
                    if (statusText == "success") {
                        newid = responseText;
                        $.showmessage('Item Updated  ' + newid);
                    } else {
                        $.showmessage('There was an error  ' );
                    }
                }});
                var branches = ''; var branche = '';
                //alert('item_type= ' + item_type +  '  id= ' +  id + ' newid= ' + newid);
                $('body').attr('fake',newid);// newid is in a different javascript thread above
                // in ajax, wait for it???
                if (item_type == 'folder' && id == 0) {
                    branches = '<li>' +
                        '<span class="folder empty"  id="item' + newid + '" objid="' + newid + '">' + 
                        '<a href="javascript:void(0);" objid="' + newid + '" class="folderlink" src="">' +
                        title + '</a></span><ul id="cmsitem_' + newid + '"></ul></li>';
                        branche = $(branches).appendTo("#cmsitem_" + parentid);
                }else if (item_type == 'cms' && id == 0) {
                    // new cms item
                    branches = '<li class="last"><span id="item' + newid + '" class="file" objid="' + newid +
                        '">' + title + '</span></li>';
                    $('#list'+parentid).children().removeClass('last');
                    branche = $(branches).appendTo("#list" + parentid);
                }else if (id > 0) {
                    // update title
                    $('#item'+id).html(title);
                }else{
                    // ??
                }
                if (id == 0) { // if it was new, update tree view
                    $("#ContentContextTree").treeview({
                        add: branche
                    });
               }
                return false;
            });
        },
        folderview: function (el) {
            var self = this;
            //remove any current active folders
            var id = $(el).attr('objid');
            $.get("/cms/viewfolder/" + id, function(data){
                $("#CmsItemFormWrapper").html(data).attr('objid',id);
                //$('#actionbar a').removeClass('current');
                $('#addcontentitem').click(function(){
                    self.cmsadd(this);
                });
                $('#addfolder').click(function(){
                    self.addfolder();
                });
                $('#editfolder').click(function(){
                    self.editfolder($('#editfolder'));
                });
                $('#sorttab').click(self.sorttab);
                $("#nodechildrenlist").sortable({stop:self.sortcomplete});
            });
        },
        /*
         * sort tab
         */
        sorttab: function () {
            $('div.boxlinks a').removeClass('current');
            $('#sorttab').addClass('current');
        },
        /*
         * Called on js completion of sort of nodes event
         */
        sortcomplete: function (event,ui) {
            var ss = '';
            $("#nodechildrenlist > li").each(function() {
                ss += $(this).attr('objid') + ',';
            });
            var folderid = $("#nodechildrenlist").attr('objid');
            $.ajax({type: "POST",url: "/cms/reorder/" + folderid ,
                data: "ids=" + ss,
                success: function(msg){
                    $.showmessage( "Data Saved: " + msg );
                }
            });
        },
        addfolder: function () {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#addfolder').addClass('current');
            var parentid = $("#CmsItemFormWrapper").attr('objid');
            if (parentid > 0) {
                $.get("/cms/addfolder/" + parentid, function(data){
                    $("#cmsformtarget").html(data);
                    self.formsetup();
                    $('#title').focus();
                    $('#parentid').val(parentid)
                });
            }else{
                alert('whoops, no parentid')
            }
        },
        cmsadd: function (el) {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#addcontentitem').addClass('current');
            var parentid = $(el).attr('objid');
            if (parentid > 0) {
                $.get("/cms/additem/", function(data){
                    $("#cmsformtarget").html(data);
                    $('#title').focus();
                    $('#parentid').val(parentid)
                    self.formsetup();
                });
            }
        },
        editfolder: function (el) {
            var self = this;
            $('div.boxlinks a').removeClass('current');
            $('#editfolder').addClass('current');
            var folderid = $(el).attr('objid');
            if (folderid > 0) {
                $.get("/cms/edit/" + folderid, function(data){
                    $("#cmsformtarget").html(data);
                    self.formsetup();
                });
            }
        }
    });
})(jQuery);


