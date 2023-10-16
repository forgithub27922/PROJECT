odoo.define('grimm_reports.Menu', function (require) {
    "use strict";

    var core = require('web.core');
    var WebInterfaceMenu = require('web_enterprise.Menu');
    var rpc = require('web.rpc');
    var session = require("web.session");

    WebInterfaceMenu.include({
        start: function () {
            var menu_bar = this.$('.o_main_navbar');
            rpc.query({
                    model: 'res.company',
                    method: 'get_color_code',
                    args: [session.user_context],
                }).then(function (result) {
                    menu_bar.css("background-color", result);
                });
            return this._super.apply(this, arguments);;
        },
    });
});