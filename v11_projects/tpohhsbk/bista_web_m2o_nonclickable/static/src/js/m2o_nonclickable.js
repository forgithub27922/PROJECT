odoo.define('bista_web_m2o_nonclickable.nonclickable', function (require) {
"use strict";

    var core = require('web.core');
    var field_m2o = require('web.relational_fields').FieldMany2One;
    var dialogs = require('web.view_dialogs');
    var _t = core._t;

    field_m2o.include({
        init: function () {
            this._super.apply(this, arguments);
            this.nodeOptions = _.defaults(this.nodeOptions, {
                quick_create: true,
                no_quick_create: true,
                no_create_edit: true,
            });
            this.can_create = false;
        },
        _searchCreatePopup: function (view, ids, context) {
            var self = this;
            return new dialogs.SelectCreateDialog(this, _.extend({}, this.nodeOptions, {
                res_model: this.field.relation,
                domain: this.record.getDomain({fieldName: this.name}),
                context: _.extend({}, this.record.getContext(this.recordParams), context || {}),
                title: (view === 'search' ? _t("Search: ") : _t("Create: ")) + this.string,
                initial_ids: ids ? _.map(ids, function (x) { return x[0]; }) : undefined,
                initial_view: view,
                disable_multiple_selection: true,
                no_create: true,
                on_selected: function (records) {
                    self.reinitialize(records[0]);
                    self.activate();
                }
            })).open();
        },
    })
});
