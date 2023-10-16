odoo.define('sms_transport.remove_export_option', function (require) {
"use strict";

var Sidebar = require('web.Sidebar');
var core = require('web.core');
var _t = core._t;
var _lt = core._lt;
    Sidebar.include({
        start: function () {
            var self = this;
            var export_label = _t("Export");
            var archive_label = _t("Archive")
            var unarchive_label = _t("Unarchive")
            var delete_label = _t("Delete")
            var sup_ctx = this.env.context.employee_supervisor
            var dri_ctx = this.env.context.employee_driver

            if (sup_ctx || dri_ctx)
            {
                self.items['other'] = $.grep(self.items['other'], function(i){
                    return i && i.label && (i.label != export_label) && (i.label != archive_label)
                    && (i.label != unarchive_label) && (i.label != delete_label);
                });
            }
            return this._super.bind(this);
        },
    });
});
