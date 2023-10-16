odoo.define('odoo_advance_search.utils', function (require) {
    'use strict';

    var ajax = require("web.ajax");
    var core = require('web.core');
    var session = require("web.session");

    var _t = core._t;

    function setAsRecordSelect($select, data=false) {
        var select2Options = {
            allowClear: true,
            multiple: $select.is('[multiple]'),
            minimumInputLength: 1,

            formatResult: function(record, resultElem, searchObj) {
                return $("<div/>", {text: record.name}).addClass('o_sign_add_partner');
            },

            formatSelection: function(record) {
                return $("<div/>", {text: record.name}).html();
            },

            ajax: {
                data: function(term, page) {
                    return { 'term': term, 'page': page };
                },
                transport: function(args) {
                    var odoo_model = this.getAttributes().search_model;
                	if (odoo_model === undefined){
                		return []
                	}
                	var context = this.getAttributes().ctx;
                    if(!context){
                    	context="{}";
                    }
                    var ctx = JSON.parse(context);
                    //ajax.rpc('/web/dataset/call_kw/'+odoo_model+'/name_search', {
                    ajax.rpc('/grimm/advance_search/call_kw/'+odoo_model, {
                        model: odoo_model,
                        method: 'name_search',
                        args: [args.data.term,session.user_context],
                        kwargs: {
                            limit: 30,
                            context: ctx
                        }
                    }).then(args.success, args.failure);
                },
                results: function(data) {
                    var last_page = data.length !== 30
                    var new_data = [];
                    _.each(data, function(record) {
                    	new_data.push({'id':record[0],'name':record[1]})
                    	/*partner['name'] = partner['name'] || '';
                        partner['email'] = partner['email'] || '';*/
                    });

                    return {'results': new_data, 'more': !last_page};
                },
                quietMillis: 250,
            },

            initSelection : function(element, callback) {
                if (element.attr('value')){
                	data = {id : parseInt(element.attr('value')), name: element.attr('title'),isNew: false }
                	//element.val('');
                	callback(data);
                }
                else{
                	callback({});
                }

            }
        };

        $select.select2('destroy');
        $select.addClass('form-control');
        $select.select2(select2Options);

//        if (data){
//        	$select.select2('data', data);
//		}

        $select.off('change').on('change', function(e) {
            if(e.added) {
        		$(e.target).attr('title',e.added.name)

            } else if(e.removed) {
            	$(e.target).attr('title','')
            }
        });
        // fix an issue select2 has to size a placeholder of an invisible input
        setTimeout(function(){
            $select.data('select2').clearSearch();
        });
    }

    return {setAsRecordSelect: setAsRecordSelect,}
});
