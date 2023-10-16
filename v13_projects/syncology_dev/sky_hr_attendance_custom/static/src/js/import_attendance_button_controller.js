odoo.define('sky_hr_attendance_custom.ImportAttendanceController', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;
    var qweb = core.qweb;

    var ImportAttendanceController = ListController.extend({
        events: _.extend({
            'click .o_button_import_attendance': '_onImportAttendance'
        }, ListController.prototype.events),
        init: function (parent, model, renderer, params) {
            return this._super.apply(this, arguments);
        },
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            var $validationButton = $(qweb.render('ImportAttendance.Buttons'));
            $validationButton.appendTo($node.find('.o_list_buttons'));
        },
        _onImportAttendance: function () {
           var self = this;
            var prom = Promise.resolve();
            prom.then(function () {
            self._rpc({
                model: 'hr.attendance',
                method: 'action_attendance',
                args: [self.employee_id]
            }).then(function (res) {

                self.do_action(res);
            });
        });
        },
    });

    return ImportAttendanceController;

});

