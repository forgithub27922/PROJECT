odoo.define('grimm_sku.listview_buttons', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var qweb = core.qweb;

    ListController.include({
        renderButtons: function ($node) {
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons = $(qweb.render('ListView.buttons', {widget: this}));
                this.$buttons.on('click', '.o_list_button_add', this._onCreateRecord.bind(this));
                this.$buttons.on('click', '.o_list_button_discard', this._onDiscard.bind(this));
                this.$buttons.on('click', '.o_button_sku', this._FetchAttributes.bind(this));
//                this.$buttons.on('click', '.o_button_scrape', this._ScrapeAttributes.bind(this));
                this.$buttons.appendTo($node);
            }
        },

        _FetchAttributes: function (ev) {
            ev.stopPropagation(); // So that it is not considered as a row leaving
            this.do_action('grimm_sku.action_ir_cron_sku_mapping')
        },
//        _ScrapeAttributes: function (ev) {
//            ev.stopPropagation(); // So that it is not considered as a row leaving
//            this.do_action('grimm_sku.action_ir_action_sku_scrape')
//        },
    });
});
