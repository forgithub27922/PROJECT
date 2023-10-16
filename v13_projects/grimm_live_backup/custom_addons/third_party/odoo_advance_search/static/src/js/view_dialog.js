odoo.define('odoo_advance_search.view_dialogs', function (require) {
"use strict";

var core = require('web.core');
var view_dialogs = require('web.view_dialogs');
var SearchView = require('web.SearchFacet');
var ListView = require('web.ListView');
var ListController = require('web.ListController');
var _t = core._t;

//Copied by Nilesh. No any changes.
var SelectCreateListController = ListController.extend({
    // Override the ListView to handle the custom events 'open_record' (triggered when clicking on a
    // row of the list) such that it triggers up 'select_record' with its res_id.
    custom_events: _.extend({}, ListController.prototype.custom_events, {
        open_record: function (event) {
            var selectedRecord = this.model.get(event.data.id);
            this.trigger_up('select_record', {
                id: selectedRecord.res_id,
                display_name: selectedRecord.data.display_name,
            });
        },
    }),
});

});