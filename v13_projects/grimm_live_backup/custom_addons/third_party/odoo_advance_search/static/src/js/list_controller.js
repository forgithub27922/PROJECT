odoo.define('odoo_advance_search.ListController', function (require) {
"use strict";

var core = require('web.core');
var BasicController = require('web.BasicController');
var ListController = require('web.ListController');
var _t = core._t;

ListController.include({
	events: _.extend({}, BasicController.prototype.events, {
    	'change thead .odoo_field_search_expan': '_change_odoo_field_search_expan',
    	'keydown thead .odoo_field_search_expan': '_onkeydownAdvanceSearch',
    }),
    _onkeydownAdvanceSearch: function (event) {
    	if (event.keyCode==13){
    		event.preventDefault();
        	event.stopPropagation();

            var search = this._controlPanel.getSearchQuery();
            var renderer = this._controlPanel.renderer;
            search = this._controlPanel.build_search_data(search);
            this.trigger_up('search', search);
    	}
    	//debugger;
    },
    _change_odoo_field_search_expan: function (event) {
    	event.preventDefault();
    	event.stopPropagation();
    	if (event.currentTarget.nodeName == "SELECT" || event.currentTarget.placeholder == "select") {
    	    var search = this._controlPanel.getSearchQuery();
            var renderer = this._controlPanel.renderer;
            search = this._controlPanel.build_search_data(search);
            this.trigger_up('search', search);
    	}
    },

});
});
